import discord
import json
import datetime
from discord.ext import tasks
from discord import slash
from difflib import SequenceMatcher
import copy



bot = slash.Bot()

@bot.event
async def on_ready():
    print("Bot is ready")
    time_check.start()

def org_send_cc(amount, org, interaction):
    data = getfile()
    if data["organisations"][org]["balance"] - amount > 0:
        data["organisations"][org]["balance"] -= amount
        savedata(data)
        return data["organisations"][org]["balance"]
    else:
        return False
    
async def org_get_cc(amount, org, interaction, account, left):
    data = getfile()
    data["organisations"][org]["balance"] += amount
    await interaction.response.send_message("Transfered " + str(amount) + "cc to " + str(org)  + " from " + str(account) + ", you have " + str(left) + "cc left", ephemeral=True)
    savedata(data)
    
def user_send_cc(amount, user, interaction):
    data = getfile()
    if data["users"][str(user)] - amount > 0:
        data["users"][str(user)] -= amount
        savedata(data)
        return data["users"][str(user)]
    else:
        return False
    
async def user_get_cc(amount, user, interaction, left):
    print("i")
    data = getfile()
    data["users"][str(user.id)] += amount
    await interaction.response.send_message("Transfered " + str(amount) + "cc to " + str(user) + " from " + str(account) +  " account, you have " + str(left) + "cc left" , ephemeral=True)
    savedata(data)
    
def org_sort():
    data = getfile()
    a = list(data["organisations"].keys())
    return a

def getfile():
    with open("storage.json" , "r") as f:
        data = json.load(f)
    return data
def savedata(data):
    with open("storage.json" , "w") as f:
        f.write(json.dumps(data))

def accounts_get1(user):
    data = getfile()
    a = ["Personal"]
    for i in data["organisations"]:
        if data["organisations"][i]["owner"] == str(user.id):
            a.append(i)
    return(a)

def accounts_get2(user):
    data = getfile()
    a = []
    for i in data["organisations"]:
        if data["organisations"][i]["owner"] == str(user.id):
            a.append(i)
    return(a)
            
async def autocompleteaccounts(interaction, value):
    return sorted(accounts_get1(interaction.user), key=lambda opt: SequenceMatcher(None, value, opt).ratio())

async def autocompleteorg(interaction, value):
    return sorted(org_sort(), key=lambda opt: SequenceMatcher(None, value, opt).ratio())

async def autodelorg(interaction, value):
    return sorted(accounts_get2(interaction.user), key=lambda opt: SequenceMatcher(None, value, opt).ratio())

async def autovote(interaction, value):
    return sorted(["for","against"], key=lambda opt: SequenceMatcher(None, value, opt).ratio())

@bot.slash_command(name="pay", description="Transfer money to another user", guild_id=907657508292792342)
@slash.option("pay_user", description="The user the money is being transferred to", required=False)
@slash.option("pay_organisation", description="The organisation the money is being transferred to", autocomplete = autocompleteorg, required=False)
@slash.option("account", description="The user the money is being transferred out of", autocomplete = autocompleteaccounts , required=True)
@slash.option("amount", description="The amount of money being transfered", min_value=0, max_value=1000, required=True)
async def pay(interaction: discord.Interaction, account: str, amount: float ,pay_user : discord.User = None , pay_organisation : str = None):
    amount = round(amount,2)
    data = getfile()
    usersend = interaction.user.id
    if not str(usersend) in data["users"]:
                data["users"][str(usersend)] = 0
                savedata(data)
    if account == "Personal" or account in data["organisations"]:
        if account == "Personal" or data["organisations"][account]["owner"] == str(interaction.user.id):
            if pay_user == None and pay_organisation == None:
                await interaction.response.send_message("Please give an account to transfer money to" , ephemeral=True)
            elif not pay_user == None and not pay_organisation == None:
                await interaction.response.send_message("Please only choose one account to send money to" , ephemeral=True)
            else:
                if account == "Personal":
                    a = user_send_cc(amount, interaction.user.id, interaction)
                else:
                    a = org_send_cc(amount, account, interaction)
                if not a == False:
                    if not pay_user == None:
                        userget = pay_user.id
                        if not str(userget) in data["users"]:
                            data = getfile()
                            data["users"][str(userget)] = 0
                            savedata(data)
                        await user_get_cc(amount, pay_user, interaction, a)
                    else:
                        await org_get_cc(amount, pay_organisation, interaction, account, a)
                else:
                    await interaction.response.send_message("Not enough cheesecoin" , ephemeral=True)
        else:
            await interaction.response.send_message("Not your organisation!" , ephemeral=True)
    else:
        await interaction.response.send_message("Organisation does not exist" , ephemeral=True)
        
@bot.slash_command(name="mp_rollcall", description="Recieve daily pay for MPs", guild_id=907657508292792342)
async def mp_rollcall(interaction: discord.Interaction):
    data = getfile()
    if not str(interaction.user.id) in data["users"]:
                data["users"][str(interaction.user.id)] = 0
                savedata(data)
    if not str(interaction.user.id) in data["claimed"]:
        data["users"][str(interaction.user.id)] +=2
        data["claimed"].append(str(interaction.user.id))
        await interaction.response.send_message("Claimed MP rollcall, balance is now " + str(data["users"][str(interaction.user.id)]) + "cc" , ephemeral=True)
        savedata(data)
    else:
        await interaction.response.send_message("Already claimed rollcall today" , ephemeral=True)
        
@bot.slash_command(name="create_org", description="create an organisation account", guild_id=907657508292792342)
@slash.option("name", description="name for this new account", required=True)
async def create_org(interaction: discord.Interaction, name : str):
    data = getfile()
    if not str(interaction.user.id) in data["users"]:
                data["users"][str(interaction.user.id)] = 0
                savedata(data)
    if not name in list(data["organisations"].keys()):
        data["organisations"][name] = {"balance" : 0, "owner" : str(interaction.user.id)}
        await interaction.response.send_message("Organisation " + name + " created" , ephemeral=True)
    else:
        await interaction.response.send_message("Organisation name already in use" , ephemeral=True)
    savedata(data)

@bot.slash_command(name="delete_org", description="destroy an organisation account", guild_id=907657508292792342)
@slash.option("name", description="name of the organisation to destroy", autocomplete = autodelorg , required=True)
async def delete_org(interaction: discord.Interaction, name : str):
    data = getfile()
    if name in data["organisations"]:
        if data["organisations"][name]["owner"] == str(interaction.user.id):
            data["users"][str(interaction.user.id)] += data["organisations"][name]["balance"]
            del data["organisations"][name]
            await interaction.response.send_message(name + " sucessfully deleted" , ephemeral=True)
            savedata(data)
        else:
            await interaction.response.send_message("Not your organisation!" , ephemeral=True)
    else:
        await interaction.response.send_message("Organisation does not exist" , ephemeral=True)

@bot.slash_command(name="vote", description="vote", guild_id=907657508292792342)
@slash.option("decision", description="for or against", autocomplete = autovote, required=True)
async def vote(interaction: discord.Interaction, decision : str):
    if str(interaction.user.id) == "762325231925854231":
        await interaction.response.send_message(str(decision), ephemeral=False)

@bot.slash_command(name="balances", description="Check your accounts and their money", guild_id=907657508292792342)
async def balances(interaction: discord.Interaction):
    data = getfile()
    if not str(interaction.user.id) in data["users"]:
                data["users"][str(interaction.user.id)] = 0
                savedata(data)
    a = "Here are your balances : \n" + "Personal : "  + str(data["users"][str(interaction.user.id)])
    for i in data["organisations"]:
        if data["organisations"][i]["owner"] == str(interaction.user.id):
            a = a + "\n" + str(i) + " : " + str(data["organisations"][i]["balance"])
    await interaction.response.send_message(a, ephemeral=True)
    

@tasks.loop(minutes=1) 
async def time_check():
    data = getfile()
    x = datetime.datetime.now()
    if int(x.strftime("%d")) != data["day"]:
        data["day"] = int(x.strftime("%d"))
        data["claimed"] = []
        savedata(data)


        
bot.run(str(json.load(open("token.txt", "r"))))
