# <u>Bub - The bot for turning D&D roleplay into xp</u>
Bub is a discord bot written in python, whose main purpose is tracking the experience gained through roleplaying in specified channel categories. It works across servers if invited to them, but sharing a single database across them. It also has functionality for tracking coins, managing the experience of users directly and in future it might get more and more features, depending on what features the server it was originally designed for needs.
If you want to use Bub on your own servers the source code is freely available, just don't claim it as your own. It was designed to work with a MySQL database. Currently it needs to be set up manually, but eventually there will be a script for setting it up.

## Functions of the bot
As stated, the primary function of Bub is to track the roleplay and converting the messages into an amount of experience, according to some specified rules. The bot also has other functions in regards to managing the experience of the accounts in it's database, such as reseting to 0, adding and removing xp and looking up the current experience of accounts using discord mentions (such as @chump)

## The word processing algorithm
In order to determine how many words of roleplay a message contains, Bub uses a custom algorithm. In order to describe it, let's divide it into steps we need to accomplish:

- locate all the specified characters which specify roleplay when surrounding words and sentences (`_ * "`)
- sort the characters into pairs (one at the beggining of roleplay, one at the end)
- filter out the pairs which overlap (`"insert *roleplay* here"` effectively becomes `"insert roleplay here"`)
- go through all the pairs which are left, counting all the words betweene them

___

### Locating the characters
This step is fairly simple: given the contents of the message in the form of a string, we go through one character at a time, writing down the position and type if it's one of our designated rp characters. This step also filters out things such as `**this** and __this__`, as those are used within discord's markdown to either embolden or underline text. The idea is that roleplay is either surrounded by quotes, or is italic, so flagging bold or underlined text as roleplay may not be entirely accurate. It's also of note that during this step, the algorithm ignores lines of the message which start with the `> ` symbol or the rest of the message after `>>>`, as those are reserved for out of character messages.

### Sorting the characters into pairs
Now that we have located the roleplay designating characters, we need to construct pairs out of them which surround the actual words of roleplay. This is done by simply going through the characters, and binding them together sequentially. During this step we also remove special characters from the message, to insure things such as `||`, which is used for spoilered text within discord, don't end up counting as words, making the tracking more accurate.

### Filtering out overlapping pairs
Given that some pairs might be contained within each other or overlap, we need to remove the redundant ones and join the overlapping ones so that we don't count the words contained in the pairs multiple times. Effectovely, two situations can arrise here, the simplified resolution of which is shown below:
 Overlap | Effective result
 --- | ---
 `"Lorem *ipsum" dolor...*` | `"Lorem ipsum dolor...*`
 `"Lorem *ipsum* dolor..."` | `"Lorem ipsum dolor..."`

### Counting words
What we are left with are pairs of our specified characters, surrounding text which is valid for roleplay. To count words, the algorithm simply splits the text contained within each pair using ` ` and counts up how many pieces we get. For cases where there's multiple space characters after each other, the "word" is an empty string and so it isn't counted towards the word total. The word total is then used as the XP amount for that message.
