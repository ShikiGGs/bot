import discord
from discord import app_commands, ui
from discord.ext import commands
import sqlite3
import random
import asyncio
import math

#await interaction.channel.create_invite(temporary=False)

# Add sqlite database 
conn = sqlite3.connect('main.sqlite')
c = conn.cursor()
# Create a table in the database to store the items in inventory
c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item TEXT,
                value INTEGER
             )''')

lower_percent = {0.85}
higher_percent = {1.25}
lower_percent_value = lower_percent.pop()
higher_percent_value = higher_percent.pop()

# etc
bot_color = 0x00ff00
guild_id = 1019452306191831040
deposit_log = 1105893315704000573
withdraw_log = 1105893884648759397
staff_deposits = 1106043654956646400
staff_withdraws = 1106043689043759214
bet_room_channels = [1105892834919325726]

# Create a new Discord client
class Myclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all(), activity = discord.Activity(type=discord.ActivityType.watching, name="Psx Cash"))
        self.synced = False  # we use this so the client doesn't sync commands more than once
        self.role = True
        self.user_id = True

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:  # check if slash commands have been synced
            # guild specific: leave blank if global (global registration can take 1-24 hours)
            await tree.sync()
            self.synced = True
            
        print(f"We have logged in as {self.user}.")

# set up slash cmd n shit 
client = Myclient()
tree = app_commands.CommandTree(client)

# Create a function that allows admins/a role to add items to the inventory of a user_id
@tree.command(name='additem', description="Add an item to a user's inventory")
@app_commands.default_permissions(administrator = True)
@app_commands.describe(value = "The value of the item you want to add")
async def additem(interaction: discord.Interaction, user: discord.Member, item: str, value: int):
    user_id = user.id
    
    # check if item's first letter is an integer and not allow it
    if item[0] == int:
        await interaction.response.send_message("Item cannot start with an integer")
        return

    if not str(value).isdigit():
        await interaction.response.send_message("Item's Value must be an integer")
        return

    # Add the item to the user_id's inventory
    #c.execute('INSERT INTO inventory VALUES (?, ?, ?)', (user_id, item.lower(), value))
    c.execute('INSERT INTO inventory (user_id, item, value) VALUES (?, ?, ?)', (user_id, item.lower(), value))
    conn.commit()

    # Send a message to the channel where the item was added
    embed = discord.Embed(description='<:check_mark:1107475827098144830> Added **{}** to <@{}>\'s inventory'.format(item.capitalize(), user_id), color=bot_color)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name='removeitem', description="Remove an item from a user's inventory")
@app_commands.default_permissions(administrator = True)
async def removeitem(interaction: discord.Interaction, user: discord.Member, item: str):
    user_id = user.id

    # Check if the item exists 
    if not c.execute('SELECT * FROM inventory WHERE user_id = ? AND item = ?', (user_id, item.lower())).fetchone():
        await interaction.response.send_message('That item does not exist in the inventory')
        return
    # Remove the item from the user_id's inventory
    c.execute('DELETE FROM inventory WHERE user_id = ? AND item = ?', (user_id, item.lower()))
    conn.commit()

    embed = discord.Embed(description='<:check_mark:1107475827098144830> Removed **{}** from <@{}>\'s inventory'.format(item.capitalize(), user_id), color=bot_color)
    # Send a message to the channel where the item was removed
    await interaction.response.send_message(embed=embed)

# Clear user's inventory
@tree.command(name='clearinv', description="Clear a user's inventory")
@app_commands.default_permissions(administrator = True)
@app_commands.describe(user = "The user whose inventory you want to clear")
async def clearinv(interaction: discord.Interaction, user: discord.Member):
    user_id = user.id

    # Check if the user's inventory exists
    if not c.execute('SELECT * FROM inventory WHERE user_id = ?', (user_id,)).fetchone():
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> This user's inventory is already empty".format(user_id), color=bot_color)
        await interaction.response.send_message(embed=embed)
        return

    # Remove the user_id's inventory
    c.execute('DELETE FROM inventory WHERE user_id = ?', (user_id,))
    conn.commit()

    # Send a message to the channel where the inventory was cleared
    embed = discord.Embed(description='<:check_mark:1107475827098144830> Cleared <@{}>\'s inventory'.format(user_id), color=bot_color)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name='inventory', description='View your inventory')
async def inventory(interaction: discord.Interaction, user: discord.Member=None):
    if user == None:
        user = interaction.user
    
    user_id = user.id

    # Get the items in the user's inventory
    items = c.execute('SELECT * FROM inventory WHERE user_id = ?', (user_id,)).fetchall()

    # Create an embed to show the items in the user's inventory
    if not items:
        await interaction.response.send_message("🔔 empty inventory")
        return
    
    else:
        items_dict = {}
        for item in items:
            if item[1] in items_dict:
                items_dict[item[1]] += 1
            else:
                items_dict[item[1]] = 1
        
        desc = ''
        for item, value in items_dict.items():
            if value == 1:
                desc += '**{}** - Value: {}\n'.format(item.capitalize() , c.execute('SELECT value FROM inventory WHERE user_id = ? AND item = ?', (user_id, item)).fetchone()[0])
            else:
                desc += '{}x **{}** - Value: {}\n'.format(value, item.capitalize(), c.execute('SELECT value FROM inventory WHERE user_id = ? AND item = ?', (user_id, item)).fetchone()[0])


        embed = discord.Embed(description=desc, color=bot_color)
        embed.set_author(name=f"{user.name}'s Inventory", icon_url=user.avatar)
        embed.set_image(url="https://cdn.discordapp.com/attachments/845376125747068988/845388140742705182/Lime_Green_Divider_by_Tyson.png")
        embed.set_footer(text=f"ID: {user_id}")

    # Send the embed to the channel where the inventory was requested
    await interaction.response.send_message(embed=embed)



# Connect to the database/
conn2 = sqlite3.connect('bets.sqlite')
c2 = conn2.cursor()

# Create the betting table if it doesn't exist
c2.execute("""CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY,
                creator_id INTEGER,
                creator_item TEXT,
                participant_id INTEGER,
                participant_item TEXT,
                winner_id INTEGER,
                winner_item TEXT,
                is_active INTEGER
            )""")
conn2.commit()

# call bot button, when no player is joining the bet, users can use this button to call a bot to join the bet with the same item, but since its a bot the bot will have 60% chance of winning the bet and 40% chance of losing the bet
class CallBotBtn(discord.ui.View):
    def __init__(self, creator_id, bet_id, creator_item):
        super().__init__()
        self.creator_id = creator_id
        self.bet_id = bet_id
        self.creator_item = creator_item
        self.value = True
    
    @discord.ui.button(label="Call Bot", style=discord.ButtonStyle.green)
    async def call_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
        # check if the button was pressed by the user who used the slash command
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message('You cannot call a bot for this bet', ephemeral=True)
        else:
            # check if the bet is still active
            if not c2.execute("SELECT * FROM bets WHERE id = ? AND is_active = 1", (self.bet_id,)).fetchone():
                await interaction.response.send_message('This bet is no longer active', ephemeral=True)
                return
            await interaction.response.send_message(f"Bot has joined the bet. Bet #{self.bet_id}")
            # Disable all buttons within the view
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)
            await asyncio.sleep(1)
            # get the creator's item
            creator_item = self.creator_item
            bot_item = self.creator_item
            # get the creator's item value
            creator_item_value = c.execute("SELECT value FROM inventory WHERE user_id = ? AND item = ?", (self.creator_id, creator_item)).fetchone()[0]
            bot_item_value = c.execute("SELECT value FROM inventory WHERE user_id = ? AND item = ?", (self.creator_id, bot_item)).fetchone()[0]

            winner_id = interaction.user.id
            winner_item = ""

            # Determine the winner and loser
            if random.random() < 0.4:
                winner_id = self.creator_id
                winner_item = creator_item
                winner_item_value = creator_item_value
                loser_id = self.bot.user.id
                loser_item = bot_item
                loser_item_value = bot_item_value
            else:
                winner_id = self.bot.user.id
                winner_item = bot_item
                winner_item_value = bot_item_value
                loser_id = self.creator_id
                loser_item = creator_item
                loser_item_value = creator_item_value

            # Update the loser's inventory
            if loser_id == self.creator_id:
                c.execute("SELECT ROWID FROM inventory WHERE user_id = ? AND item = ?", (loser_id, loser_item))
                rowid = c.fetchone()[0]
                c.execute("DELETE FROM inventory WHERE ROWID = ?", (rowid,))
            # Update the winner's inventory
            if winner_id == self.creator_id:
                c.execute('INSERT INTO inventory VALUES (?, ?, ?)', (winner_id, winner_item.lower(), winner_item_value))
                conn.commit()
            # Update the bet in the database
            c2.execute("""UPDATE bets SET winner_id = ?""", (winner_id))
            conn2.commit()
            embedR = discord.Embed(title='Bet Result <:bet:1097411487129141248>', description=f'Bet #`{self.bet_id}` has been resolved.\n\n**Winner:** <@{winner_id}> 🎉 \nEarned: {loser_item.capitalize()}\nValue gained: +{loser_item_value}', color=bot_color)
            embedR.set_footer(text="Use /inventory to check your newly won items")
            await interaction.channel.send(embed=embedR)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        # check if the button was pressed by the user who used the slash command
        print(interaction.user.id)
        print(self.creator_id)
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message('You cannot cancel this bet', ephemeral=True)
        else:
            bet_id = c2.lastrowid
            c2.execute("UPDATE bets SET is_active = 0 WHERE id = ?", (bet_id,))
            conn2.commit()
            # Disable all buttons within the view
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)
            embed=discord.Embed(description=f"**Bet #{self.bet_id} cancelled**\nCreator: <@{self.creator_id}>", color=bot_color)
            await interaction.response.send_message(embed=embed)

# Function to create a new bet
@tree.command(name='bet', description='Gamble an item')
#@app_commands.checks.cooldown(1, 60, key = lambda i: (i.user.id))
async def bet(interaction: discord.Interaction, item: str):

    creator_id = interaction.user.id
    creator_item = item.lower()
    global is_active
    is_active = 1

    # Check if the user has the item in their inventory
    result = c.execute('SELECT value FROM inventory WHERE user_id = ? AND item = ?', (creator_id, creator_item)).fetchone()
    if not result:
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> You don't have {} in your inventory.".format(item[0].upper() + item[1:].lower()), color=bot_color)
        await interaction.response.send_message(embed=embed)
        return

    # CHeck if the user is already in a bet
    if c2.execute('SELECT * FROM bets WHERE creator_id = ? AND is_active = 1', (creator_id,)).fetchone():
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> You are already in a bet.", color=bot_color)
        embed.set_footer(text="Click the cancel button to end it")
        await interaction.response.send_message(embed=embed)
        return

    # Insert the bet into the database
    c2.execute("""INSERT INTO bets (creator_id, creator_item, is_active) 
                    VALUES (?, ?, ?)""", (creator_id, creator_item, is_active))
    conn2.commit()

    # Get the bet ID
    bet_id = c2.lastrowid

    # Get the value of the item
    inventory_value = result[0]
    # Send a message with the bet ID
    channel = interaction.guild.get_channel(random.choice(bet_room_channels))
    await interaction.response.send_message(f'Your bet has been created in {channel.mention}. Bet ID: `{bet_id}`', ephemeral=True)
    embed = discord.Embed(title=f'Bet Created - Room #{bet_id}', description=f'__waiting for user..__\n({math.ceil(int(inventory_value) * float(lower_percent_value))} - {math.floor(int(inventory_value) * float(higher_percent_value))})', color=bot_color)
    embed.add_field(name=f'{creator_item.capitalize()} - Value: {inventory_value}', value='Bet Room ID: `{}`'.format(bet_id))
    embed.set_footer(text=f"Room opened by {interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar)
    bet_msg = await channel.send(embed=embed, view=CallBotBtn(creator_id, bet_id, creator_item))

    """
    await asyncio.sleep(600)

    # if still active
    if c2.execute('SELECT is_active FROM bets WHERE id = ?', (bet_id,)).fetchone()[0] == 1:
        # Update the bet to mark it as inactive
        c2.execute("UPDATE bets SET is_active = 0 WHERE id = ?", (bet_id,))
        conn2.commit()

        # Send a message indicating that the bet has expired
        embedF = discord.Embed(description=f"<:cross_mark:1107475788476981338> Room #{bet_id} has expired and is no longer active.", color=bot_color)
        embedF.set_footer(text=f"Room opened by {interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar)
        message = await interaction.original_response()
        await message.edit(embed=embedF, view=None)
    """

@tree.command(name='join', description='Join a bet')
async def join(interaction: discord.Interaction, bet_id:int, item:str):
    participant_id = interaction.user.id
    participant_item = item.lower()

    # Get the bet from the database
    c2.execute("""SELECT * FROM bets WHERE id = ? AND is_active = 1""", (bet_id,))
    bet = c2.fetchone()

    creator_id = bet[1]
    creator_item = bet[2]

    if not bet:
        await interaction.response.send_message("Invalid bet ID")
        return

    # Check if the user has already joined another bet
    if c2.execute('SELECT * FROM bets WHERE participant_id = ? AND is_active = 1', (participant_id,)).fetchone():
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> You have already created a bet", color=bot_color)
        embed.set_footer(text="Click the cancel button to create a new bet")
        await interaction.response.send_message(embed=embed)
        return

    participant_value = c.execute('SELECT value FROM inventory WHERE user_id = ? AND item = ?', (participant_id, participant_item)).fetchone()
    creator_value = c.execute('SELECT value FROM inventory WHERE user_id = ? AND item = ?', (creator_id, creator_item)).fetchone()

    # check if the participant has the item in their inventory
    if not participant_value:
        embed = discord.Embed(description=f"<:cross_mark:1107475788476981338> You don't have {participant_item.capitalize()} in your inventory.", color=bot_color)
        await interaction.response.send_message(embed=embed)
        print(participant_value)
        print(creator_value)
        return
    else:
        print(participant_value[0])
        print(creator_value[0])

        # Make sure the participant is not the same as the creator
        if participant_id == creator_id:
            embed = discord.Embed(description=f"<:cross_mark:1107475788476981338> You cannot join your own bet.", color=bot_color)
            await interaction.response.send_message(embed=embed)
            return
        # Make sure the bet is still active
        elif bet[3] == 0:
            embed = discord.Embed(description=f"<:cross_mark:1107475788476981338> Bet is no longer active.", color=bot_color)
            await interaction.response.send_message(embed=embed)
            return
        elif int(creator_value[0]) * float(lower_percent_value) > int(participant_value[0]):
            embed = discord.Embed(description=f"<:cross_mark:1107475788476981338> Item's value is too less compared to the creator's item. Must be above 85% value of the creator's item", color=bot_color)
            await interaction.response.send_message(embed=embed)
            return
        elif int(creator_value[0]) * float(higher_percent_value) < int(participant_value[0]):
            embed = discord.Embed(description=f"<:cross_mark:1107475788476981338> Item's value is too high compared to the creator's item. Must be below 115% value of the creator's item", color=bot_color)
            await interaction.response.send_message(embed=embed)
            return
        else:
            # Insert the participant into the bet
            c2.execute("""UPDATE bets SET participant_id = ?, participant_item = ? WHERE id = ?""", (participant_id, item, bet_id))
            conn2.commit()
            # set bet active to 0
            c2.execute("""UPDATE bets SET is_active = 0 WHERE id = ?""", (bet_id,))

            channel = interaction.guild.get_channel(random.choice(bet_room_channels))
            #channel = interaction.guild.get_channel(983191248523378759)
            await interaction.response.send_message(f"Sucessfully joined Bet Room #{bet_id}")
            await interaction.channel.send(f"<@{creator_id}><@{participant_id}> \nCheck " + channel.mention + " to find the winner! 🪙")
            embed = discord.Embed(title=f'Room ID #{bet_id}', description=f'{interaction.user.mention} has joined the bet\n\n<@{creator_id}> vs {interaction.user.mention}', color=bot_color)
            embed.set_footer(text=f"winner is being choosen...")
            await channel.send(embed=embed)
            await channel.send("<a:loading:1099184825585389668>")
            await asyncio.sleep(4)

            winner_id = interaction.user.id
            winner_item = ""

            # Determine the winner and loser
            if random.random() < 0.4:
                winner_id = self.creator_id
                winner_item = creator_item
                winner_item_value = creator_item_value
                loser_id = client.user.id
                loser_item = bot_item
                loser_item_value = bot_item_value
            else:
                winner_id = client.user.id
                winner_item = bot_item
                winner_item_value = bot_item_value
                loser_id = self.creator_id
                loser_item = creator_item
                loser_item_value = creator_item_value

            # Remove the loser's item from their inventory
            #c.execute("""DELETE FROM inventory WHERE user_id = ? AND item = ?""", (loser_id, loser_item))
            #conn.commit()

            c.execute("SELECT ROWID FROM inventory WHERE user_id = ? AND item = ?", (loser_id, loser_item))
            rowid = c.fetchone()[0]
            c.execute("DELETE FROM inventory WHERE ROWID = ?", (rowid,))
            # Update the winner's inventory
            c.execute('INSERT INTO inventory VALUES (?, ?, ?)', (winner_id, loser_item.lower(), loser_item_value))
            conn.commit()
            # Update the bet in the database
            c2.execute("""UPDATE bets SET winner_id = ?""", (winner_id))
            conn2.commit()
            embedR = discord.Embed(title='Bet Result <:bet:1097411487129141248>', description=f'Bet #`{bet_id}` has been resolved.\n\n**Winner:** <@{winner_id}> 🎉 \nEarned: {loser_item.capitalize()}\nValue gained: +{loser_item_value}', color=bot_color)
            embedR.set_footer(text="Use /inventory to check your newly won items")
            await channel.send(embed=embedR)

# a command that shows history of all bets that happened in the server
@tree.command(name = 'betlogs', description='Shows the list of all bets')
@app_commands.default_permissions(administrator=True)
async def bet_logs(interaction: discord.Interaction):
    
    # Get all the bets from the database
    bets = c2.execute("""SELECT * FROM bets WHERE is_active = 0""").fetchall()

    # If there are no bets, send an error message
    if not bets:
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> There are no bets done in this server yet", color=bot_color)
        await interaction.response.send_message(embed=embed)
        return
    else:
        logs = ''
        for bet in bets:
            logs += f"**Bet #{bet[0]}**\n Creator: <@{bet[1]}> : Participant: <@{bet[3]}>\nCreator Item: {bet[2].capitalize()}\nParticipant Item: {bet[4].capitalize()}\nWinner: <@{bet[5]}>\n\n"

        embed = discord.Embed(title='Bet Logs <:bet:1097411487129141248>', description=logs, color=bot_color)
        await interaction.response.send_message(embed=embed)

class DepModal(ui.Modal, title="Deposit Item Value Modal"):
    def __init__(self, item, username, user):
        super().__init__()
        self.item = item
        self.username = username
        self.user = user
        self.value = None

    DepositItemValue = ui.TextInput(
        label=f"Deposit Item's Value",
        style=discord.TextStyle.short,
        placeholder="value..",
        min_length=1, max_length=10,
        required=True)

    async def on_submit(self, interaction: discord.Interaction):
        item_value = self.DepositItemValue.value
        # Add the item from the user's inventory
        c.execute('INSERT INTO inventory VALUES (?, ?, ?)', (self.user.id, self.item.lower(), item_value))
        conn.commit()
        embed = discord.Embed(description=f"<:check_mark:1107475827098144830> Deposit request accepted\n\n**Username:** {self.username}\n**Item:** {self.item}\n", color=bot_color)
        await interaction.response.send_message(embed=embed)
        dep_log_channel = interaction.guild.get_channel(deposit_log)
        embed = discord.Embed(description=f"**{self.username}** has sucessfully deposited **{self.item}**", color=bot_color)
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        embed.set_footer(text=f"Item Value: {item_value}")
        # ping the user while sending the embed but make the ping outisde the embed
        await dep_log_channel.send(f"<@{self.user.id}>", embed=embed)

class ConfirmDepositBtn(discord.ui.View):
    def __init__(self, item, username, user):
        super().__init__()
        self.item = item
        self.username = username
        self.user = user
        self.value = None

    @discord.ui.button(label="Confirm Deposit", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DepModal(item=self.item, username=self.username, user=self.user))
        self.value = False
        self.stop()
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> Deposit request declined", color=bot_color)
        await interaction.response.send_message(embed=embed, view=self)
        self.value = False
        self.stop()

@tree.command(name="manualdeposit", description="Manually deposits an item to the bot")
async def manual_dep(interaction: discord.Interaction, item: str, username: str):
    # Check if the item is valid
    """
    if item.lower() not in items:
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> Invalid item", color=bot_color)
        await interaction.response.send_message(embed=embed)
        return
    """
    # check if item's first letter is an integer and not allow it
    if item[0] == int:
        await interaction.send_message("Item cannot start with an integer")
        return
    
    embed = discord.Embed(description="<:check_mark:1107475827098144830> Deposit request created (It May Take 4-12 Hours For You To Get The Pets)\n**<:PSXCASH:1107491910999879680> Please Gift The Pet To: `GWA_4` (In Order To Get The Pet In Our Bot)**", color=bot_color)
    embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
    embed.add_field(name="Username:", value=username)
    embed.add_field(name="Item:", value=item)
    await interaction.response.send_message(embed=embed)

    confirm_dep_channel = interaction.guild.get_channel(staff_deposits)
    cEmbed = discord.Embed(description=f"**{interaction.user.mention}** has created a deposit request\n\nUsername: **{username}**\nItem: **{item}**", color=bot_color)
    cEmbed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
    await confirm_dep_channel.send(embed=cEmbed, view=ConfirmDepositBtn(item, username, interaction.user))

class ConfirmWithdrawBtn(discord.ui.View):
    def __init__(self, item, username, user):
        super().__init__()
        self.item = item
        self.username = username
        self.user = user
        self.value = None

    @discord.ui.button(label="Confirm Withdraw", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Withdraw request accepted")
        # remove the item from the user's inventory
        c.execute("SELECT ROWID FROM inventory WHERE user_id = ? AND item = ?", (self.user.id, self.item.lower()))
        rowid = c.fetchone()[0]
        c.execute("DELETE FROM inventory WHERE ROWID = ?", (rowid,))
        conn.commit()
        withdraw_log_channel = interaction.guild.get_channel(withdraw_log)
        embed = discord.Embed(description=f"**{self.username}** has sucessfully withdrawed **{self.item}**", color=bot_color)
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        await withdraw_log_channel.send(f"<@{self.user.id}>", embed=embed)
        # dm the user saying the item has been withdrawn
        user = interaction.guild.get_member(self.user.id)
        DMEmbed = discord.Embed(description=f"<:check_mark:1107475827098144830> Withdraw request accepted\n\nYour Item **{self.item}** has been withdrawn\nCheck your item in PSX", color=bot_color)
        DMEmbed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        await user.send(embed=DMEmbed)
        self.value = False
        self.stop()
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> Deposit request declined", color=bot_color)
        await interaction.response.send_message(embed=embed, view=self)
        # dm the user saying the item withdraw has been declined
        user = interaction.guild.get_member(self.user.id)
        DMEmbed = discord.Embed(description=f"<:cross_mark:1107475788476981338> Withdraw request declined\n\nYour Item **{self.item}** has been declined from withdrawl\n", color=bot_color)
        DMEmbed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        await user.send(embed=DMEmbed)
        self.value = False
        self.stop()

@tree.command(name = "manualwithdraw", description="Manually withdraws an item from the bot")
async def manual_withdraw(interaction: discord.Interaction, item: str, username: str):
    # check if item is in user's inventory
    if not c.execute('SELECT * FROM inventory WHERE user_id = ? AND item = ?', (interaction.user.id, item.lower())).fetchone():
        embed = discord.Embed(description="<:cross_mark:1107475788476981338> You don't have this item in your inventory", color=bot_color)
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(description="<:check_mark:1107475827098144830> Withdraw request created (It May Take 4-12 Hours In Order For You To Get The Pets)", color=bot_color)
    embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
    embed.add_field(name="Username:", value=username)
    embed.add_field(name="Item:", value=item)
    await interaction.response.send_message(embed=embed)

    confirm_withdraw_channel = interaction.guild.get_channel(staff_withdraws)
    cEmbed = discord.Embed(description=f"**{interaction.user.mention}** has created a withdraw request\n\nUsername: **{username}**\nItem: **{item}**", color=bot_color)
    cEmbed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
    await confirm_withdraw_channel.send(embed=cEmbed, view=ConfirmWithdrawBtn(item, username, interaction.user))



# MISC CMD
@tree.command(name = 'purge', description='Deletes an amount of messages')
@app_commands.default_permissions(administrator=True)
async def purge(interaction: discord.Interaction, amount : int):
    if amount > 100:
        embed = discord.Embed(description="<:error:1010472224530120725> I can't purge over 100 messages!", color=bot_color)
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        await interaction.response.send_message(embed=embed)
    elif amount <= 100:
        #embed = discord.Embed(description=f"{interaction.user.mention} purged {amount} messages", color=bot_color)
        #embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        await interaction.response.defer()
        await interaction.channel.purge(limit=amount+1)

@tree.command(name="ping", description="Shows the bot's latency")
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(description=f"🏓 Pong! {round(client.latency * 1000)}ms", color=bot_color)
    embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
    await interaction.response.send_message(embed=embed)

@tree.command(name="avatar" , description="Shows the avatar of a user")
async def avatar(interaction: discord.Interaction, user: discord.User = None):
    if user == None:
        user = interaction.user
    embed = discord.Embed(title=f"{user.name}'s avatar", color=bot_color)
    embed.set_image(url=user.avatar_url)
    await interaction.response.send_message(embed=embed)

bot_token = "MTA5NzUxNjQ3NDg3ODM5NDU2MA.GzNBWw.OM1awPHpyiVfxGkENHLWrarcNVSVUMtl-PTbWU"
client.run(bot_token)