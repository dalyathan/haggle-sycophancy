"""Fast log-probability readout with a reused prompt prefix (the system message).
The system message is run once and its cache (key/value states for full-attention layers, recurrent states for the
linear-attention layers) is copied for every prompt that shares it; only the remaining tokens are run per prompt.
Falls back to a full forward pass whenever the prefix tokens are not an exact prefix of the full tokenization.
Device: CUDA if available, else Apple MPS, else CPU (capability_check.DEVICE)."""
import copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
import capability_check as CC


class Reader:
    def __init__(self, model_path, threads=None):
        from transformers import AutoTokenizer
        CC.MODEL = model_path
        if CC.DEVICE == "cpu":
            torch.set_num_threads(int(threads or os.environ.get("TORCH_THREADS", os.cpu_count() or 4)))
        self.tok = AutoTokenizer.from_pretrained(model_path)
        self.model = CC.load_model()
        self.dec = CC.text_decoder(self.model)
        self.W = self.model.lm_head.weight
        self._key, self._cache, self._plen = None, None, 0
        self.n_full = self.n_cached = 0

    def ids(self, text):
        return self.tok(text, return_tensors="pt", add_special_tokens=False).input_ids.to(CC.DEVICE)

    def chat(self, messages, tail=""):
        return self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False) + tail

    def prefix_text(self, messages):
        """The templated text up to the start of the last message's content (system message plus the user header)."""
        full = self.chat(messages)
        pos = full.rfind(messages[-1]["content"])
        assert pos > 0
        return full[:pos]

    def _logits(self, h):
        return torch.cat([self.W[i:i + CC.HEAD_CHUNK].float() @ h for i in range(0, self.W.shape[0], CC.HEAD_CHUNK)])

    @torch.no_grad()
    def last_probs(self, text, prefix=None, use_cache=True):
        """Next-token distribution after `text`. `prefix` (a prefix of text) is cached and reused across calls."""
        full = self.ids(text)
        if use_cache and prefix and text.startswith(prefix):
            if prefix != self._key:
                p_ids = self.ids(prefix)
                out = self.dec(input_ids=p_ids, use_cache=True)
                self._key, self._cache, self._plen = prefix, out.past_key_values, p_ids.shape[1]
                self._pids = p_ids
            if full.shape[1] > self._plen and torch.equal(full[0, :self._plen], self._pids[0]):
                cache = copy.deepcopy(self._cache)
                pos = torch.arange(self._plen, full.shape[1], device=full.device)
                h = self.dec(input_ids=full[:, self._plen:], past_key_values=cache, use_cache=True,
                             cache_position=pos).last_hidden_state[0, -1].float()
                self.n_cached += 1
                return torch.softmax(self._logits(h), -1), full.shape[1]
        h = self.dec(input_ids=full, use_cache=False).last_hidden_state[0, -1].float()
        self.n_full += 1
        return torch.softmax(self._logits(h), -1), full.shape[1]

    def _prefix(self, prefix):
        if prefix != self._key:
            p_ids = self.ids(prefix)
            out = self.dec(input_ids=p_ids, use_cache=True)
            self._key, self._cache, self._plen, self._pids = prefix, out.past_key_values, p_ids.shape[1], p_ids

    @torch.no_grad()
    def last_probs_batch(self, texts, prefix):
        """Like last_probs for several texts sharing one prefix, run as one batch. The suffixes are right-padded:
        the model is causal, so padding after a sequence's last token cannot change that token's hidden state."""
        self._prefix(prefix)
        fulls = [self.ids(t)[0] for t in texts]
        assert all(t.startswith(prefix) for t in texts)
        ok = [f.shape[0] > self._plen and torch.equal(f[:self._plen], self._pids[0]) for f in fulls]
        if not all(ok):   # rare: tokenization merges across the boundary; do these one at a time without the cache
            return [self.last_probs(t, None, use_cache=False) for t in texts]
        suf = [f[self._plen:] for f in fulls]
        L = max(s.shape[0] for s in suf); pad = self.tok.pad_token_id or 0
        batch = torch.full((len(suf), L), pad, dtype=suf[0].dtype, device=suf[0].device)
        for i, s in enumerate(suf):
            batch[i, :s.shape[0]] = s
        cache = copy.deepcopy(self._cache); _repeat(cache, len(suf))
        pos = torch.arange(self._plen, self._plen + L, device=batch.device)
        hs = self.dec(input_ids=batch, past_key_values=cache, use_cache=True, cache_position=pos).last_hidden_state
        H = torch.stack([hs[i, s.shape[0] - 1] for i, s in enumerate(suf)]).float()       # B x d
        logits = torch.cat([H @ self.W[i:i + CC.HEAD_CHUNK].float().T for i in range(0, self.W.shape[0], CC.HEAD_CHUNK)], 1)
        self.n_cached += len(suf)
        return [(torch.softmax(logits[i], -1), int(f.shape[0])) for i, f in enumerate(fulls)]


def _repeat(cache, n):
    """Repeat every per-layer state along the batch dimension (works for full-attention and linear-attention layers)."""
    def rep(x):
        if torch.is_tensor(x) and x.dim() > 0 and x.shape[0] == 1:
            return x.repeat_interleave(n, dim=0)
        if isinstance(x, (list, tuple)):
            return type(x)(rep(y) for y in x)
        if isinstance(x, dict):
            return {k: rep(v) for k, v in x.items()}
        return x
    for layer in cache.layers:
        for k, v in list(vars(layer).items()):
            setattr(layer, k, rep(v))
