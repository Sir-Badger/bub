# Bub - The bot for turning D&D roleplay into xp
Bub is a discord bot written in python, whose main purpose is tracking the experience gained through roleplaying in specified channel categories. It works across servers if invited to them, but sharing a single database across them. It also has functionality for tracking coins, managing the experience of users directly and in future it might get more and more features, depending on what features the server it was originally designed for needs.
If you want to use Bub on your own servers the source code is freely available, just don't claim it as your own. It was designed to work with a MySQL database. Currently it needs to be set up manually, but eventually there will be a script for setting it up.

## Functions of the bot
As stated, the primary function of Bub is to track the roleplay and converting the messages into an amount of experience, according to some specified rules desribed [further](#xp-system). Currently the bot has the following functions:
- Scanning messages sent inside specified categories for roleplay
- Basic tracking of coins (platinum, electrum, gold, silver and copper)
- The ability to see the current experience statistics of members of the server
- A "top 10" command
- tools for reseting, or otherwise modifying a member's experience

## XP system
Ambrozia's xp system works like this:

When a message is sent inside of the specified roleplay categories, it gets scanned for valid rp. If there is some, the words of rp are counted. Every user can only earn 7200 xp every 24 hours. (300 xp per hour)

## Counting the words
For counting the words, Bub uses a custom word processing algorythm, which checks for words surrounded by one of the following characters: `"`,`_` or `*` while ignoring paragraphs starting with `>` and `-`. Empty strings and the following characters do not count as valid words when counting: `|`, `"`, `*`, `_` and `

For a more in depth explanation of how the word counting actually works, the source code and explanation of the algorythm can be found [here](https://github.com/Sir-Badger/word_counter).
