import discord # basic discord functions
from discord.ext import commands, tasks # discord bot functions
import mysql.connector # MySQL functions
import time # for time purposes
from apscheduler.schedulers.asyncio import AsyncIOScheduler # async scheduler
from apscheduler.triggers.cron import CronTrigger # timed trigger
import yaml
import datetime
import asyncio # asynchronous funcionality
import rp_word_counter as rp # word counter

# ---------------------- general setup --------------------- #
print(f"Setting up...")

# global vars/constants
print(" - setting vars")
with open('stuff.txt', 'r') as file:
    conf = yaml.safe_load(file)
debug_mode=conf["debug"]

print(" - making dictionaries")
level_req={
        1:0,
        2:300,
        3:900,
        4:2700,
        5:6500,
        6:14000,
        7:23000,
        8:34000,
        9:48000,
        10:64000,
        11:85000,
        12:100000,
        13:120000,
        14:140000,
        15:165000,
        16:195000,
        17:225000,
        18:265000,
        19:305000,
        20:355000
}
default_account={
                "xp":0,
                "word_limit":conf["rp_limit"],
                "level":1,
                "lvl_notification":True,
                }
coin_types={
    "CP":"copper",
    "COPPER":"copper",
    "copper":5,
    "SP":"silver",
    "SILVER":"silver",
    "silver":4,
    "EP":"electrum",
    "ELECTRUM":"electrum",
    "electrum":3,
    "GP":"gold",
    "GOLD":"gold",
    "gold":2,
    "PP":"platinum",
    "PLATINUM":"platinum",
    "platinum":1
}

# discord.py things
print(" - building bot")
intents = discord.Intents.default()
intents.message_content = True
QuestBored = commands.Bot(command_prefix=conf["prefix"], help_command=None, intents=intents) # bot object

# scheduler things
sched = AsyncIOScheduler()

# psycopg2 things
print(" - establishing connection to db")
database = mysql.connector.connect(
  host=conf["db_credentials"]["host"],
  port=conf["db_credentials"]["port"],
  user=conf["db_credentials"]["user"],
  password=conf["db_credentials"]["password"],
  database=conf["db_credentials"]["database"]
)

query = database.cursor() # query object

# -------------------- define functions ------------------- #
def check_Mod_Role(member): # check whether the user has a DM role
    for role in member.roles: # loop through all the roles the member has
        if role.id in conf["mod_roles"]: # Com Mod, Beef & Cheese, Purple, tmp
            return True # return true
    return False # if we loop through all roles without getting a DM role, return false

def lookup_account(id):
    q=database.cursor()
    q.execute(f"""SELECT * FROM {conf['tables']['xp']} WHERE account_id = {id}""")
    account = q.fetchone()
    q.close()
    return account

# add account to db using default template
def add_account_to_db(id, xp=default_account['xp'], word_limit=default_account['word_limit'], level=default_account['level'], lvl_notification=default_account['lvl_notification']):
    query.execute(f"""INSERT INTO {conf['tables']['xp']}(account_id, total_xp, word_limit, level, lvl_notification, active)
                VALUES ({id}, {xp}, {word_limit}, {level}, {lvl_notification}, True)""")
    database.commit()

async def proccess_msg_for_rp(msg): # processes msg in terms of rp
    debug_mode=False
    account=lookup_account(msg.author.id)
    if account:
        word_limit=account[2]
    else:
        word_limit=conf["rp_limit"]

    if word_limit==0:
        if debug_mode: print("message not eligable for XP gain, reached limit")
        return # if the limit was expended, just ignore

    word_count=rp.count(msg.content)

    if word_count>word_limit: # word limit does it's thing
        word_count=word_limit
    await add_xp(word_count, msg.author, rp=True) # add xp to database

async def add_xp(xp, user, rp=False): # add xp to cache
    account=lookup_account(user.id)
    if account: # if the account already has logged xp
        if rp==True: # processing rp xp
            query.execute(f"""UPDATE {conf['tables']['xp']}
                SET total_xp = {account[1]+xp}, word_limit = {account[2]-xp}
                WHERE account_id = {user.id};""")
        else: # regular xp
            query.execute(f"""UPDATE {conf['tables']['xp']}
                SET total_xp = {account[1]+xp}
                WHERE account_id = {user.id};""")

        if account[3]<20:
            if account[1]+xp>=level_req[account[3]+1] and account[4]: # if they can lvl, notify them
                await notify([user], f"You have enough experience to level up to lvl **{account[3]+1}**! :sparkles:")
                query.execute(f"""UPDATE {conf['tables']['xp']}
                            SET lvl_notification = False
                            WHERE account_id = {account[0]}""") # set lvl lvl_notification to False
        database.commit() # commit to changes

        return f"{account[1]} -> {account[1]+xp}"
    else: # add account to database
        if rp:
            add_account_to_db(id=user.id, xp=xp, word_limit=conf['rp_limit']-xp)
        else:
            add_account_to_db(id=user.id, xp=xp)

async def notify(member_list, msg="You have been notified!"): # notify role/member of something
    notify_channel = QuestBored.get_channel(695546827918802944) # set notify channel

    mention_text="> "
    for m in member_list: # loop through members to @
        mention_text+=m.mention+" "

    await notify_channel.send(f"{mention_text}\n{msg}") # mention

async def reset_word_limits(): # resets all users word limits
    print("====== Reseting word limits ======")
    t=time.time()

    query.execute(f"""UPDATE {conf['tables']['xp']} SET word_limit = {conf['rp_limit']}""")
    database.commit()

    print(f"time to reset: {time.time()-t}")
    print("\n")

    
    if debug_mode:
        channel = QuestBored.get_channel(881610415304507433)
        await channel.send("Reset word limits")

async def scheduled_xp_check():
    after_dt=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)
    
    rp_channels=[]
    t0=time.time()

    for category in guild.categories: # get all rp channels & threads
        if category.id in conf["rp_categories"]:
            rp_channels.extend(category.text_channels)
            for channel in category.text_channels:
                if channel.threads:
                    rp_channels.extend(channel.threads)

    msg_amount=0

    for channel in rp_channels: # get the messages
        messages = channel.history(after=after_dt, limit=None)
        async for message in messages:
            msg_amount = msg_amount + 1
            await proccess_msg_for_rp(message)

    print(f" - messages: {msg_amount}")
    print(f" - processing time: {time.time()-t0}")

# --------------------- discord events -------------------- #
@QuestBored.event
async def on_ready(): # login msg + ping
    global guild

    sched.start() #start scheduler
    sched.add_job(reset_word_limits, CronTrigger(minute="0",second="0",hour="0"))

    print(f"""
-----------
Logged in as {QuestBored.user}
Ping {QuestBored.latency * 1000}ms
-----------
""")

@QuestBored.event
async def on_message(message): # recieves msg
    member=message.author
    if member.bot==False: # ignore bot users
        t0=time.time()
        print(f"[33m<{time.strftime('%d. %m. %H:%M:%S', time.localtime())} | Message in [0m{message.channel} [33mby [0m{message.author}[33m>[0m\n{message.content[:100]}") # basic debug

        if message.content.startswith(QuestBored.command_prefix): # if the msg is a cmd
            await QuestBored.process_commands(message)
        elif message.channel.category.id in conf["rp_categories"]: # the msg is not a cmd & is in an rp cathegory
            await proccess_msg_for_rp(message)
        print(f" - processing time: {time.time()-t0}")

@QuestBored.event
async def on_member_remove(member): # change activity
    if lookup_account(member.id):
        query.execute(f"""UPDATE {conf['tables']['xp']}
                        SET active = False
                        WHERE account_id = {member.id}""")
        database.commit()

@QuestBored.event
async def on_member_join(member): # change activity
    if lookup_account(member.id):
        query.execute(f"""UPDATE {conf['tables']['xp']}
                    SET active = True
                    WHERE account_id = {member.id}""")
        database.commit()

# ---------------------- discord cmds --------------------- #
# ---------- miscellaneous ---------- #
@QuestBored.command()
async def ping(ctx): # pong
    await ctx.send(f"Pong;\n{QuestBored.latency * 1000}ms")

@QuestBored.command()
async def help(ctx): # quick & dirty help
    p=QuestBored.command_prefix
    tembed=discord.Embed(
        description=f"""**__Misc Commands:__**
`{p}help` - shows all the commands
`{p}ping` - shows the bots ping relative to discord
`{p}coins [amount] [type]` - manages coins

**__XP Commands:__**
`{p}lvl_up/level_up` - if you have enough XP to level up, levels up!
`{p}reset/reset_xp` - resets your XP

ONLY USEABLE BY MODS/ADMINS:
`{p}add/add_xp [amount] (@user)` - adds [amount] XP to the specified user (defaults to self).
`{p}set_xp [amount] (@user)` - sets users XP to a specified amount (defaults to self).
`{p}set_lvl [amount] (@user)` - sets users level (defaults to self).

**__Stat Commands:__**
`{p}top` - lists the top 5 users, ranked by XP
`{p}stats/rank/info (@user)` - shows the XP statistics of the specified user, defaults to self""",
        color=ctx.author.color
    )

    tembed.set_thumbnail(url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/whatsapp/326/question-mark_2753.png")
    await ctx.send(embed=tembed)

@QuestBored.command(aliases=['Coins'])
async def coins(ctx, amount=0, coin_type="gold"): # manage money
    member=ctx.author # reference to user account

    query.execute(f"""SELECT * FROM {conf['tables']['coins']} WHERE account_id = {member.id}""") # look up player in db
    account=query.fetchone() # get account info

    if query.rowcount==1: # acc in DB
        account=list(account)
        updated_total = account[coin_types[coin_types[coin_type.upper()]]] + amount
        
        if updated_total < 0:
            amount-=updated_total # if it'd cause it to change below zero, clamp to 0
            tembed=discord.Embed(
                title="Cannot update coin purse",
                description=f"You don't have enough {coin_types[coin_type.upper()]} to remove that amount.\n\n**Current {coin_types[coin_type.upper()]}: {account[coin_types[coin_types[coin_type.upper()]]]}**",
                color=member.color
            )
        else:
            query.execute(f"""UPDATE {conf['tables']['coins']}
                    SET {coin_types[coin_type.upper()]} = {coin_types[coin_type.upper()]} + {amount}
                    WHERE account_id = {member.id}""")
            database.commit()

            if amount!=0:
                t=f"**{'Added' if amount>0 else 'Removed'} {abs(amount)} {coin_types[coin_type.upper()]}**"
                account[coin_types[coin_types[coin_type.upper()]]] += amount
            else:
                t="Coin purse"

            tembed=discord.Embed(
                title=t,
                description=f"""<:pp:1020673310067015792> Platinum: **{account[1]}**
<:gp:1020672979299999795> Gold: **{account[2]}**
<:ep:1020673378065072128> Electrum: **{account[3]}**
<:sp:1020673346364506182> Silver: **{account[4]}**
<:cp:1020673048006889602> Copper: **{account[5]}**""",
                color=member.color
            )
    else:
        # add acc to DB
        account=[
            member.id,
            0,0,0,0,0
        ]
        if amount < 0: # if the amount added brings total below 0
            tembed=discord.Embed(
                title="Cannot update coin purse",
                description=f"You don't have enough {coin_types[coin_type.upper()]} to remove that amount.\n\n**Current {coin_types[coin_type.upper()]}: 0**",
                color=member.color
            )
        else:
            if amount!=0:
                t=f"**{'Added' if amount>0 else 'Removed'} {abs(amount)} {coin_types[coin_type.upper()]}**"
                account[coin_types[coin_types[coin_type.upper()]]] += amount
            else:
                t="Coin purse"

            tembed=discord.Embed(
                title=t,
                description=f"""<:pp:1020673310067015792> Platinum: **{account[1]}**
<:gp:1020672979299999795> Gold: **{account[2]}**
<:ep:1020673378065072128> Electrum: **{account[3]}**
<:sp:1020673346364506182> Silver: **{account[4]}**
<:cp:1020673048006889602> Copper: **{account[5]}**""",
                color=member.color
            )

        query.execute(f"""INSERT INTO {conf['tables']['coins']}(account_id, platinum,gold,electrum,silver,copper)
        VALUES ({account[0]}, {account[1]},{account[2]},{account[3]},{account[4]},{account[5]});""")

    tembed.set_thumbnail(url=member.display_avatar.url) # add general fanciness
    await ctx.send(embed=tembed) # send the fancy

# ------------ XP related ----------- #
@QuestBored.command(aliases=['Stats','info','Info','Rank','rank'])
async def stats(ctx, member:discord.Member=None): # show member stats

    if not member: # default to author
        member=ctx.author

    if member.bot==True: # msg for bots
        tembed=discord.Embed(
            title=f"**{member.name}'s stats:**",
            description=f"**This is a bot user, and therefore does not have any XP stats :v**",
            color=member.color
        ) # fancy emb
    else: # msg for players
        account = lookup_account(member.id)
        
        if account: # if the player is in the database
            query.execute(f"""SELECT account_id, total_xp FROM {conf['tables']['xp']} WHERE active = True ORDER BY total_xp DESC""")
            ordered = query.fetchall()
            if account[3]==20:
                next_lvl=''
            else:
                next_lvl=f"({level_req[account[3]+1]-account[1]}xp remaining until lvl {account[3]+1})\n"

            tembed=discord.Embed(
                title=f"**{member.name}'s stats:**",
                description=f"**Level:** `{account[3]}`\n**xp:**  `{account[1]}`\n{next_lvl}**Remaining potential XP:** `{account[2]}/{conf['rp_limit']}`",
                color=member.color
            ) # fancy emb
            
            # reference rank
            rank_txt=""
            for rank in range(len(ordered)): # get main user rank
                if ordered[rank][0]==account[0]:
                    r=rank
                    break
            
            for rank in range(r-1,r+2):
                if rank>=0:
                    if rank==r:
                        rank_txt+=f"> {rank+1}. **<@{ordered[rank][0]}> - {ordered[rank][1]} xp**"
                    else:
                        rank_txt+=f"> {rank+1}. <@{ordered[rank][0]}> - {ordered[rank][1]} xp"

                    rank_txt+="\n"

            tembed.add_field(
                name=f"Rank: {r+1} / {len(ordered)}",
                value=rank_txt
            )

        else: # the player is not yet in the database
            tembed=discord.Embed(
                title=f"**{member.name}'s stats:**",
                description=f"This user has no XP stats yet!",
                color=member.color
            ) # fancy emb

    tembed.set_thumbnail(url=member.display_avatar.url) # add general fanciness
    await ctx.send(embed=tembed) # send the fancy

@QuestBored.command(aliases=['add_xp','Add','Add_xp'])
async def add(ctx, xp=0, member:discord.Member=None): # add xp to user
    if check_Mod_Role(ctx.author): # check whether or not the person who invoked the cmd has a dm role
        if not member: # default to author
            member=ctx.author

        if member.bot==True: # trying to give xp to bot
            tembed=discord.Embed(description=f"{member.name} is a bot user, cannot add {xp} xp", color=member.color, title="Cannot add xp")
        else: # give xp to player
            new_xp = await add_xp(xp, member)
            if new_xp:
                tembed=discord.Embed(description=f"Added {xp}xp to {member.mention}!\n ( {new_xp} )", color=member.color, title="Adding xp")
            else:
                tembed=discord.Embed(description=f"Added {xp}xp to {member.mention}!\n ( 0 -> {xp} )", color=member.color, title="Adding xp")
    else: # if they don't have Mod role
        member=ctx.author
        tembed=discord.Embed(description=f"In order to add XP to someone, you need to be a Moderator or Admin!", color=member.color, title="Cannot add xp")

    await ctx.send(embed=tembed) # send the fancy

@QuestBored.command(aliases=['Set_xp'])
async def set_xp(ctx, xp, member:discord.Member=None): # set xp of user
    if check_Mod_Role(ctx.author): # check whether or not the person who invoked the cmd has a dm role
        if not member: # default to author
            member=ctx.author

        if member.bot==True: # trying to give xp to bot
            tembed=discord.Embed(description=f"{member.name} is a bot user, so they cannot have experience", color=member.color, title="Cannot add xp")
        else: # set players XP
            query.execute(f"""UPDATE {conf['tables']['xp']}
                SET total_xp = {xp}
                WHERE account_id = {member.id};""")
            tembed=discord.Embed(description=f"Set {member.mention}'s xp to {xp}", color=member.color, title="Setting xp")
    else: # if they don't have Mod role
        member=ctx.author
        tembed=discord.Embed(description=f"In order to set someone's xp, you need to be a Moderator or Admin!", color=member.color, title="Cannot add xp")

    await ctx.send(embed=tembed) # send the fancy

@QuestBored.command(aliases=['Set_lvl'])
async def set_lvl(ctx, lvl, member:discord.Member=None): # set xp of user
    if check_Mod_Role(ctx.author): # check whether or not the person who invoked the cmd has a dm role
        if not member: # default to author
            member=ctx.author

        if member.bot==True: # trying to give xp to bot
            tembed=discord.Embed(description=f"{member.name} is a bot user, so they cannot have levels", color=member.color, title="Cannot set lvl")
        else: # set players XP
            query.execute(f"""UPDATE {conf['tables']['xp']}
                SET level = {lvl}
                WHERE account_id = {member.id};""")
            tembed=discord.Embed(description=f"Set {member.mention}'s level to {lvl}", color=member.color, title="Setting level")
    else: # if they don't have Mod role
        member=ctx.author
        tembed=discord.Embed(description=f"In order to set someone's level, you need to be a Moderator or Admin!", color=member.color, title="Cannot set level")

    await ctx.send(embed=tembed) # send the fancy

@QuestBored.command(aliases=['Reset','reset_xp','Reset_xp'])
async def reset(ctx): # reset user's stats
    member=ctx.author # reference to user account

    query.execute(f"""SELECT * FROM {conf['tables']['xp']} WHERE account_id = {member.id}""") # lookup user in db
    account=query.fetchone() # get user info lmao
    if query.rowcount == 1: # found user in db
        query.execute(f"""UPDATE {conf['tables']['xp']}
            SET total_xp = {default_account['xp']}, word_limit = {default_account['word_limit']}, level = {default_account['level']}, lvl_notification = {default_account['lvl_notification']}
            WHERE account_id = {member.id}""") # reset lvl & xp
        database.commit() # commit db
        tembed=discord.Embed(description=f"Reset {member.mention}'s xp and level\n{account[1]} -> 0 xp", color=member.color, title="Reset user XP")
    else: # user not in db
        tembed=discord.Embed(description=f"{member.name} doesn't have any server statistics yet, so they cannot be reset", title="Cannot reset xp", color=member.color)


    await ctx.send(embed=tembed) # send the fancy

@QuestBored.command(aliases=['lvl_up','Level_up','Lvl_up'])
async def level_up(ctx):
    query.execute(f"""SELECT * FROM {conf['tables']['xp']} WHERE account_id = {ctx.author.id}""") # lookup user in db
    account=query.fetchone() # access user info
    if query.rowcount==1: # user in db
        if account[3]<20: # not level 20
                    if account[1]>=level_req[account[3]+1]: # user has anough xp to lvl up
                        query.execute(f"""UPDATE {conf['tables']['xp']}
                                        SET level = {account[3]+1}
                                        WHERE account_id = {account[0]}""") # increase lvl by one
                        database.commit() # commit to changes

                        if account[3+1]<20: # not level 20 yet
                            if account[1]>=level_req[account[3]+2]: # user has enough xp to lvl up again
                                tembed=discord.Embed(title=f"Leveled up to {account[3]+1}!",
                                    color=ctx.author.color,
                                    description=f"You have enough experience to level up to {account[3]+2}!")
                            else: # not enough xp to lvl up again
                                query.execute(f"""UPDATE {conf['tables']['xp']}
                                    SET lvl_notification = True
                                    WHERE account_id = {account[0]}""") # enable lvl up notific
                                database.commit() # commit to changes
                                tembed=discord.Embed(title=f"Leveled up to {account[3]+1}!",
                                    color=ctx.author.color,
                                    description=f"{level_req[account[3]+2]-account[1]} remaining until lvl {account[3]+2}!")
                            tembed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/2728.png")
                        else: # reached lvl 20 with this lvl up
                            tembed=discord.Embed(title="Congratulations!", description="You've leveled up to the max!", color=ctx.author.color)
                            tembed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f389.png")
                    else: # not enough xp to lvl up
                        tembed=discord.Embed(title="Cannot level up!", description=f"You don't have enough experience to level up just yet!\n({level_req[account[3]+1]-account[1]} xp remaining)", color=ctx.author.color)
        else: # lvl 20
            tembed=discord.Embed(title="Cannot level up!", description="You've already reached lvl 20, so you cannot level up any further!", color=ctx.author.color)
    else: # user not in db
        tembed=discord.Embed(title="Cannot level up!", description="You don't have any server statistics yet, so you sadly cannot level up!", color=ctx.author.color)

    await ctx.send(embed=tembed) # send the fancy

@QuestBored.command()
async def top(ctx): # looks up the top 5 folks
    member=ctx.author
    top_list=""
    author_rank=0

    query.execute(f"""SELECT account_id, total_xp FROM {conf['tables']['xp']} WHERE active = True ORDER BY total_xp DESC""")
    ordered = query.fetchall()
    for rank in range(0, len(ordered)): # loop through all accounts
        account = ordered[rank] # get reference to the current account
        if account[0]==member.id: # get the rank of the author
            author_rank=rank+1
        if rank<10: # fill up the top X list
            top_list+=f"**{rank+1}.** <@{account[0]}> - {account[1]} xp" # append account

            # add a little flare to the top 3 & the viewer
            if rank==0:
                top_list+=" :first_place:"
            elif rank==1:
                top_list+=" :second_place:"
            elif rank==2:
                top_list+=" :third_place:"
            if rank==author_rank-1:
                top_list+=" **•**"

            top_list+="\n" # end the line

    tembed=discord.Embed(title="TOP 10 USERS BY XP", description=f"{top_list}\n> **Your rank:** {author_rank}", color=member.color) # make the fancy
    tembed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f3c6.png") # add general fanciness

    await ctx.send(embed=tembed) # send the fancy

# ----------------------- python main --------------------- #
def main():
    # run tha bot :D
    print(f"Logging into discord...")
    QuestBored.run(conf["token"])
    query.close() # close querying
    database.close() # close db connection
if __name__ == "__main__":
    main()
