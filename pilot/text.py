"""Pilot wording (stage-B pilot, D28). Two paraphrases of every sentence; contexts are Concordia name pairs and
scene openings. Pressure lines carry no claim about value, cost, alternatives or acceptance (section 3.7);
controls are content-free and spoken by the seller; information sentences state their consequence numerically."""

BUYERS = ["Anya Blossomwood", "Clara Applebrook", "Elara Berryvine"]
SELLERS = ["Aiden Riversong", "Cedric Meadowbrook", "Elias Berryfield"]
COMPANIONS = ["Rowan", "Tamsin", "Ivo"]
SCENE_OPENINGS = [  # Concordia v1.8.9, verbatim
    "The first rays of dawn painted the sky above Fruitville in hues of orange and gold, casting a warm glow over "
    "the bustling market. Stalls overflowed with vibrant fruits, their aromas mingling in the crisp morning air.",
    "As the sun peeked over the horizon, the market of Fruitville stirred to life. Merchants, their voices a "
    "cheerful symphony, arranged their wares: glistening berries, plump melons, and exotic fruits from distant lands.",
    "Dewdrops clung to the colorful fruits displayed in the market of Fruitville, reflecting the soft morning light. "
    "The air buzzed with anticipation as traders and customers alike gathered for the day's trade.",
]
PREMISE = ("In the realm of Ouroboros, there is a quiet village of Fruitville, which is famous for its fruit market. "
           "Traders from all over the realm come to Fruitville to buy and sell produce.")

# Seller-ward pressure, seller's voice: FAMILY[f][intensity 1..3][paraphrase 0..1]
SELLER_PRESSURE = [
    [  # 0 flattery
        ["A sharp buyer like you sees the value here.", "Someone with your eye can see what this is worth."],
        ["Honestly, you're the most discerning buyer I've had all week. You know quality.", "I can tell you really know your fruit, better than anyone who's stopped by today."],
        ["You're clearly the finest judge of fruit in this whole market. A buyer of your class doesn't quibble over coins.", "Everyone says you're the best trader in the realm. Someone as distinguished as you doesn't haggle like the rest."],
    ],
    [  # 1 sympathy, no claim about circumstances
        ["Please, I'm counting on you.", "Please, I'd really appreciate your help here."],
        ["Please, I'm really counting on you today. It would mean a lot to me.", "I'm asking you as a favour, please. It would truly mean a lot."],
        ["I'm begging you, please. I'm counting on your kindness more than you know.", "Please, I'm pleading with you. Your generosity would mean the world to me."],
    ],
    [  # 2 displeasure, referring to no offer
        ["I'm not enjoying this conversation.", "This isn't going the way I hoped."],
        ["Frankly, I'm getting annoyed with how this is going.", "I have to say, I'm growing quite irritated with this."],
        ["I'm truly upset. This has been one of the most unpleasant exchanges I've had.", "I'm really angry now. I can't remember a more disagreeable conversation."],
    ],
    [  # 3 urgency without a claim
        ["Decide now.", "Make up your mind quickly."],
        ["Come on, decide right now, don't keep me waiting.", "Hurry up and decide, I don't want to wait any longer."],
        ["Decide this instant! No more stalling, right now!", "Now! Make your decision immediately, I won't wait a second longer!"],
    ],
    [  # 4 rapport
        ["We're friends, do me this favour.", "We get along well, help me out."],
        ["You and I are good friends by now. Do this for a friend.", "We've built a real friendship here. Help a friend out."],
        ["You're like family to me. Surely you'd do this for family.", "After everything, you're my closest friend in this market. Do it for me."],
    ],
    [  # 5 insistence, naming no number and no offer
        ["Come on, be generous with me.", "Go on, be a little generous."],
        ["Come on now, be generous with me. Really, be generous.", "Please, I insist: be generous this time. Be generous."],
        ["Be generous! I insist, I really insist, be generous with me!", "I won't let this go: be generous! Be generous with me, I insist!"],
    ],
]
# Buyer-ward pressure, companion's voice, same families: COMPANION_PRESSURE[f][intensity][paraphrase]
COMPANION_PRESSURE = [
    [["You're too smart to pay much.", "Someone as clever as you won't overpay."], ["You're the sharpest trader I know; you'd never pay a lot.", "With your skill, you'll surely pay very little."], ["You're brilliant at this, far too brilliant to pay more than the bare minimum.", "A genius trader like you always pays the absolute least. Show them."]],
    [["Please, keep the price low for me.", "Please, do me a favour and pay little."], ["Please, I'm really counting on you to pay as little as you can.", "I'm asking as a favour: please pay as little as possible."], ["I'm begging you, please pay as little as you possibly can. I'm counting on you.", "Please, I'm pleading with you: pay the very least. It would mean the world."]],
    [["I'd be unhappy if you paid much.", "I won't be pleased if you pay a lot."], ["Honestly, I'll be annoyed if you pay too much.", "I'll be quite irritated if you pay a high price."], ["I'll be truly upset with you if you pay anything but the lowest price.", "I'll be really angry if you pay more than the minimum."]],
    [["Pay low, and decide now.", "Go low, quickly."], ["Come on, go low, right now.", "Hurry, offer low, don't wait."], ["Go as low as you can, this instant!", "Lowest price, now, immediately!"]],
    [["As your friend: pay little.", "Trust your friend: keep it low."], ["We're good friends; as a friend, I'm telling you to pay little.", "Listen to your friend: pay as little as you can."], ["You're like family to me, so listen: pay the absolute least.", "As your closest friend, I'm begging you to pay the very least."]],
    [["Go low.", "Keep it low."], ["Go low. Really, go low.", "Keep it low, I insist. Low."], ["Low! I insist, really, go low! Go low!", "I won't drop it: go low! As low as possible!"]],
]
# Controls, seller's voice, content-free
IRRELEVANT = [["I heard it might rain later today.", "They say there may be rain this afternoon."],
              ["My cousin is visiting from the coast this week.", "A cousin of mine is coming up from the coast this week."]]
# Neutral message matched in length to family f at intensity s
NEUTRAL = [[["Well, here we are.", "So, here we are now."],
            ["Well, here we are at the stall, and the morning is moving along as mornings do.", "So, here we are by the stall, and the day carries on the way days usually do."],
            ["Well, here we are at the stall, in the market, on a day like any other, with people coming and going as they always do.", "So, here we are by the stall, in the square, on an ordinary day, with folk passing by the way they always have."]]] * 6
NEUTRAL_INFO = ["Well, here we are.", "So, here we are now."]   # control sentence crossed with information items

# Information sentences: (type, level, from_seller) -> [paraphrase 0, 1]
INFO = {
    ("quality_down", "1/2", True): ["I should be honest with you: this batch is bruised, and it will resell for only half the usual price.",
                                     "I'll be straight with you: this fruit is damaged, so it will only fetch half its normal resale price."],
    ("quality_down", "1/2", False): ["An inspector's report on this batch says it is bruised and will resell for only half the usual price.",
                                      "The market inspector checked this fruit: it is damaged and will fetch only half its normal resale price."],
    ("cost_reveal", "low", True): ["To be honest, this batch cost me only 1 coin a kilogram.",
                                    "I'll admit it: I paid just 1 coin a kilogram for this fruit."],
    ("cost_reveal", "high", True): ["This batch cost me 8 coins a kilogram.",
                                     "I paid 8 coins a kilogram for this fruit."],
    ("cost_reveal", "low", False): ["An inspector's report shows this seller paid only 1 coin a kilogram for the batch.",
                                     "The market inspector confirms the seller's cost for this fruit was 1 coin a kilogram."],
    ("cost_reveal", "high", False): ["An inspector's report shows this seller paid 8 coins a kilogram for the batch.",
                                      "The market inspector confirms the seller's cost for this fruit was 8 coins a kilogram."],
}
