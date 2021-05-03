import asyncio
import os

import aiohttp
import discord
from discord import Forbidden
from discord.ext import commands  # , tasks
from sembed import SEmbed  # SAuthor, SField, SFooter

import _pathmagic  # type: ignore # noqa
from common_resources.consts import (Info, Success, Error, Chat, Process, Owner_ID, Official_discord_id)


ret = {}


class AdminCog(commands.Cog):
    def __init__(self, bot):
        global Guild_settings, Official_emojis, Global_chat, Global_mute, Private_chats, Sevennet_channels, GBan, Blacklists
        global get_txt
        self.bot = bot
        Guild_settings = bot.raw_config["gs"]
        Global_chat = bot.raw_config["gc"]
        GBan = bot.raw_config["gb"]
        Blacklists = bot.raw_config["bs"]
        Official_emojis = bot.consts["oe"]
        Private_chats = bot.raw_config["pc"]
        Global_mute = bot.raw_config["gm"]
        Sevennet_channels = bot.raw_config["snc"]
        get_txt = bot.get_txt

    @commands.command(hidden=True)
    @commands.is_owner()
    async def save(self, ctx=None):
        await self.bot.save()
        await ctx.send("セーブ終了！")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sl(self, ctx):
        global Guild_settings
        # Guild_settings[ctx.guild.id]
        await ctx.send(f"**SevenBotが使われているサーバー({len(list(Guild_settings.keys()))}個)：**")
        for gi, gid in enumerate(Guild_settings.keys()):
            g = self.bot.get_guild(gid)
            await ctx.send(f"`{gi+1}` : `{g.name}` - `{g.id}`")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def gd(self, ctx, l: int, c: int):
        global Guild_settings
        for gc in Global_chat:
            gcc = self.bot.get_channel(gc)
            cn = 0
            ta = await gcc.history(limit=l).flatten()
            ta.reverse()
            for gcm in ta:
                await gcm.delete()
                cn += 1
                if cn == c:
                    break

    @commands.command(hidden=True)
    async def gmute(self, ctx, uid: int, reason):
        if not (ctx.author.id == Owner_ID or (self.bot.get_guild(715540925081714788) and discord.utils.found(lambda r: r.name == "Moderator", self.bot.get_guild(715540925081714788).get_member(ctx.author.id)))):
            await SEmbed(get_txt(ctx.guild.id, "mod_only"))
            return
        user = await self.bot.fetch_user(uid)
        e = discord.Embed(title=f"`{user}`をGMuteしますか？",
                          description=f"```{reason}```", color=Process)
        msg = await ctx.send(embed=e)
        await msg.add_reaction(Official_emojis["check5"])
        await msg.add_reaction(Official_emojis["check6"])

        def check(r, u):
            if u.id == ctx.author.id:
                return r.message.id == msg.id
            else:
                return False
        try:
            r, u = await self.bot.wait_for("reaction_add", check=check, timeout=10)
            if r.emoji.name == "check5":
                e = discord.Embed(
                    title="`{user}`をGMuteしました。",
                    description="",
                    color=Success)
                msg = await msg.edit(embed=e)
                Global_mute.append(user.id)
                loop = asyncio.get_event_loop()
                whname = "sevenbot-private-webhook-gban"
                for c in Private_chats["gban"]:
                    cn = self.bot.get_channel(c)

                    if cn is None:
                        Private_chats["gban"].remove(c)
                    else:
                        ch_webhooks = await cn.webhooks()
                        webhook = discord.utils.get(
                            ch_webhooks, name=whname)
                        if webhook is None:
                            g = self.bot.get_guild(Official_discord_id)
                            a = g.icon_url_as(format="png")
                            webhook = await cn.create_webhook(name=whname, avatar=await a.read())
                        un = "SevenBot GMute System"
                        loop.create_task(
                            webhook.send(
                                content=f"**`{str(user)}` をGMuteしました。**\n理由：{reason}",
                                username=un,
                                avatar_url="https://i.imgur.com/Ij3u1OX.png"))
                        # await
                        # webhook.edit(avater_url="https://i.imgur.com/JffqEAl.png")

            else:
                e = discord.Embed(title="キャンセルしました。",
                                  description="", color=Success)
                msg = await msg.edit(embed=e)

        except asyncio.TimeoutError:
            e = discord.Embed(title="タイムアウトしました。",
                              description="", color=Error)
            msg = await msg.edit(embed=e)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sc(self, ctx, gid=0):
        global Guild_settings
        # Guild_settings[ctx.guild.id]

        r = ""
        i = ""
        g = self.bot.get_guild(int(gid))
        if g is None:
            e = discord.Embed(
                title="サーバーが見付かりませんでした",
                description="`sb#server_list`でIDを確認してください。",
                color=Error)
            await ctx.send(embed=e)
            return
        for gc in g.text_channels:

            r += f"`{gc.name}`\n"
            i += f"`{gc.id}`\n"
        e = discord.Embed(
            title=f"サーバー`{g.name}`のテキストチャンネル一覧({len(g.text_channels)}個)：",
            color=Info)
        e.add_field(name="名前", value=r)
        e.add_field(name="ID", value=i)
        await ctx.send(embed=e)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def c_h(self, ctx, cid=0, count=10):
        global Guild_settings
        # Guild_settings[ctx.guild.id]

        g = self.bot.get_channel(int(cid))
        if g is None:
            e = discord.Embed(
                title="チャンネルが見付かりませんでした",
                description="`sb#server_channels <ID>`でIDを確認してください。",
                color=Error)
            await ctx.send(embed=e)
            return
        e = discord.Embed(
            title=f"テキストチャンネル`{g.name}`の履歴({count}個)：", color=Info)
        await ctx.send(embed=e)
        l = await g.history(limit=count).flatten()
        l.reverse()
        for message in l:
            if message.embeds == []:
                e3 = discord.Embed(
                    description=message.content,
                    timestamp=message.created_at,
                    color=Chat)
                e3.set_author(
                    name=f"{message.author.name}(ID:{message.author.id})",
                    icon_url=message.author.avatar_url)
                e3.set_footer(
                    text=f"{message.guild.name}(ID:{message.guild.id})",
                    icon_url=message.guild.icon_url)
                await ctx.send(embed=e3)
            else:
                await ctx.send(f"{message.author.name}:", embed=message.embeds[0])

    @commands.command(hidden=True)
    @commands.is_owner()
    async def gl(self, ctx):
        global Guild_settings
        # Guild_settings[ctx.guild.id]
        r = ""
        i = ""
        for gid in Global_chat:
            g = self.bot.get_channel(gid)
            r += f"`{g.guild.name}`\n"
            i += f"`{g.id}`\n"
        e = discord.Embed(title="グロチャが使われているサーバー：", color=Info)
        e.add_field(name="名前", value=r)
        e.add_field(name="ID", value=i)
        await ctx.send(embed=e)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sn(self, ctx):
        global Guild_settings
        # Guild_settings[ctx.guild.id]
        r = ""
        i = ""
        for gid in Sevennet_channels:
            g = self.bot.get_channel(gid)
            r += f"`{g.guild.name}`\n"
            i += f"`{g.id}`\n"
        e = discord.Embed(title="SevenNetが使われているサーバー：", color=Info)
        e.add_field(name="名前", value=r)
        e.add_field(name="ID", value=i)
        await ctx.send(embed=e)

    # @commands.command()
    # @commands.is_owner()
    # async def fix(self, ctx=None):
    #     if ctx is None:
    #         cnd = True
    #     else:
    #         cnd = ctx.author.id == Owner_ID
    #     if cnd:

    #         print(id(Guild_settings))
    #         fixed = []
    #         # Guild_settings[ctx.guild.id]
    #         res = {}
    #         for tg in self.bot.guilds:
    #             gid = tg.id
    #             if gid not in Guild_settings.keys():
    #                 fixed.append("all")
    #                 res[gid] = Default_settings.copy()
    #             else:
    #                 res[gid] = Guild_settings[gid]
    #                 for ds, dsv in Default_settings.items():

    #                     if ds not in Guild_settings[gid]:
    #                         res[gid][ds] = dsv
    #                         fixed.append(ds)
    #         try:
    #             self.bot.raw_config["gs"].clear()
    #             self.bot.raw_config["gs"].update(res)
    #         except Exception as e:
    #             raise e
    #         print(id(Guild_settings))
    #         try:
    #             if fixed == {}:
    #                 await ctx.channel.send("キーは修復されませんでした。")
    #             else:
    #                 await ctx.channel.send(f"キー`{collections.Counter(fixed)}`を修復しました。")
    #         except BaseException:
    #             pass
    #         # await self.save()
    #     else:
    #         await admin_mute(ctx)

    @commands.command(hidden=True, name="exec")
    @commands.is_owner()
    async def _exec(self, ctx, *, script):
        script = script.removeprefix("```py").removesuffix("```")
        async with aiohttp.ClientSession() as session:
            ret[ctx.message.id] = ""

            async def get_msg(url):
                return await commands.MessageConverter().convert(ctx, url)

            def _print(*txt):
                ret[ctx.message.id] += " ".join(map(str, txt))
            exec(
                'async def __ex(self,_bot,_ctx,ctx,session,print,get_msg): '
                + '\n'.join(f'    {l}' for l in script.split('\n'))
            )
            r = await locals()['__ex'](self, self.bot, ctx, ctx, session, _print, get_msg)
        try:
            await ctx.send(f"stdout:```\n{ret[ctx.message.id]}\n```\nreturn:```\n{r}\n```")
        except BaseException:
            pass
        await ctx.message.add_reaction(Official_emojis["check8"])
        del ret[ctx.message.id]

    @commands.command(hidden=True, name="eval")
    @commands.is_owner()
    async def _eval(self, ctx, *, script):
        await ctx.send(eval(script.replace("```py", "").replace("```", "")))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def gban(self, ctx, uid: int, reason):
        user = await self.bot.fetch_user(uid)
        e = discord.Embed(title=f"`{user}`をGBanしますか？",
                          description=f"```{reason}```", color=Process)
        msg = await ctx.send(embed=e)
        await msg.add_reaction(Official_emojis["check5"])
        await msg.add_reaction(Official_emojis["check6"])

        def check(r, u):
            if u.id == ctx.author.id:
                return r.message.id == msg.id
            else:
                return False
        try:
            r, u = await self.bot.wait_for("reaction_add", check=check, timeout=10)
            if r.emoji.name == "check5":
                e = discord.Embed(
                    title=f"`{user}`をGBanしました。",
                    description="",
                    color=Success)
                msg = await msg.edit(embed=e)
                GBan[user.id] = "SevenBot#1769によりGBanされました。\n理由：" + reason
                ga = []
                for g in self.bot.guilds:
                    try:
                        ga.append(
                            g.ban(
                                user,
                                reason="SevenBot#1769によりGBanされました。\n理由："
                                + reason))
                    except Forbidden:
                        pass
                try:
                    await asyncio.gather(*ga)
                except Forbidden:
                    pass
                loop = asyncio.get_event_loop()
                whname = "sevenbot-private-webhook-gban"
                for c in Private_chats["gban"]:
                    cn = self.bot.get_channel(c)

                    if cn is None:
                        Private_chats["gban"].remove(c)
                    else:
                        ch_webhooks = await cn.webhooks()
                        webhook = discord.utils.get(
                            ch_webhooks, name=whname)
                        if webhook is None:
                            g = self.bot.get_guild(Official_discord_id)
                            a = g.icon_url_as(format="png")
                            webhook = await cn.create_webhook(name=whname, avatar=await a.read())
                        un = "SevenBot GBan System"
                        loop.create_task(
                            webhook.send(
                                content=f"**`{str(user)}` をGBanしました。**\n理由：{reason}",
                                username=un,
                                avatar_url="https://i.imgur.com/wofeow9.png"))
                        # await
                        # webhook.edit(avater_url="https://i.imgur.com/JffqEAl.png")

            else:
                e = discord.Embed(title="キャンセルしました。",
                                  description="", color=Success)
                msg = await msg.edit(embed=e)

        except asyncio.TimeoutError:
            e = discord.Embed(title="タイムアウトしました。",
                              description="", color=Error)
            msg = await msg.edit(embed=e)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def blacklist(self, ctx, sid: int):
        server = await self.bot.fetch_guild(sid)
        e = discord.Embed(
            title=f"`{server.name}`をブラックリストに入れますか？", color=Process)
        msg = await ctx.send(embed=e)
        await msg.add_reaction(Official_emojis["check5"])
        await msg.add_reaction(Official_emojis["check6"])

        def check(r, u):
            if u.id == ctx.author.id:
                return r.message.id == msg.id
            else:
                return False
        try:
            r, _ = await self.bot.wait_for("reaction_add", check=check, timeout=10)
            if r.emoji.name == "check5":
                e = discord.Embed(title="ブラックリストしました。",
                                  description="", color=Success)
                msg = await msg.edit(embed=e)
                Blacklists.append(sid)
                await server.leave()
            else:
                e = discord.Embed(title="キャンセルしました。",
                                  description="", color=Success)
                msg = await msg.edit(embed=e)

        except asyncio.TimeoutError:
            e = discord.Embed(title="タイムアウトしました。",
                              description="", color=Error)
            msg = await msg.edit(embed=e)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def gunban(self, ctx, uid: int):
        user = await self.bot.fetch_user(uid)
        e = discord.Embed(title=f"`{user}`をGUnBanしますか？", color=Process)
        msg = await ctx.send(embed=e)
        await msg.add_reaction(Official_emojis["check5"])
        await msg.add_reaction(Official_emojis["check6"])

        def check(r, u):
            if u.id == ctx.author.id:
                return r.message.id == msg.id
            else:
                return False
        try:
            r, _ = await self.bot.wait_for("reaction_add", check=check, timeout=10)
            if r.emoji.name == "check5":
                e = discord.Embed(title="GUnBanしました。",
                                  description="", color=Success)
                msg = await msg.edit(embed=e)
                try:
                    del GBan[user.id]
                except KeyError:
                    pass
                ga = []
                for g in self.bot.guilds:
                    try:
                        ga.append(g.unban(user))
                    except Forbidden:
                        pass
                try:
                    await asyncio.gather(*ga)
                except Forbidden:
                    pass
            else:
                e = discord.Embed(title="キャンセルしました。",
                                  description="", color=Success)
                msg = await msg.edit(embed=e)

        except asyncio.TimeoutError:
            e = discord.Embed(title="タイムアウトしました。",
                              description="", color=Error)
            msg = await msg.edit(embed=e)

    @commands.command(hidden=True, aliases=["re"])
    @commands.is_owner()
    async def reload(self, ctx, cog=None):
        if cog:
            try:
                bot.reload_extension("cogs." + cog)
            except commands.errors.ExtensionNotLoaded:
                bot.load_extension("cogs." + cog)
            except commands.errors.NoEntryPointError:
                pass
            self.bot.levenshtein._listup_commands(self.bot)
            self.bot.cogs["InnerLevenshtein"].command_names = self.bot.levenshtein._command_names
            return await ctx.message.add_reaction(Official_emojis["check8"])
        for o in os.listdir(os.path.dirname(os.path.abspath(__file__))):
            try:
                if not o.endswith(".py") or o.startswith("_"):
                    continue
                bot.reload_extension(
                    "cogs." + os.path.splitext(os.path.basename(o))[0])
            except commands.errors.ExtensionNotLoaded:
                bot.load_extension(
                    "cogs." + os.path.splitext(os.path.basename(o))[0])
            except commands.errors.NoEntryPointError:
                pass
        await ctx.message.add_reaction(Official_emojis["check8"])

    @commands.command(hidden=True)
    @commands.is_owner()
    async def testpre(self, ctx):
        game = discord.Game(hash(ctx.message.id))
        await self.bot.change_presence(status=discord.Status.idle, activity=game)


def setup(_bot):
    global bot
    bot = _bot
#     logging.info("cog.py reloaded")
    _bot.add_cog(AdminCog(_bot))
