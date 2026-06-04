import discord
from discord.ext import commands

from config import FOOTBALL_TEAMS


class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="teamstats", help="Show member counts for all football teams")
    async def team_stats(self, ctx: commands.Context) -> None:
        """
        Display member counts for all configured football team roles.
        Usage: !teamstats
        """
        embed = discord.Embed(
            title="⚽ Football Team Statistics",
            description=f"Member count for all clubs in {ctx.guild.name}",
            color=discord.Color.green(),
        )

        total_members = 0
        teams_found = []
        teams_not_found = []

        for team_name in FOOTBALL_TEAMS:
            role = discord.utils.get(ctx.guild.roles, name=team_name)

            if role:
                member_count = len(role.members)
                total_members += member_count
                teams_found.append((role, member_count))
            else:
                teams_not_found.append(team_name)

        teams_found.sort(key=lambda entry: entry[1], reverse=True)

        if teams_found:
            team_list = []
            for role, count in teams_found:
                team_list.append(f"{role.mention} - **{count}** members")

            embed.add_field(
                name="📊 Club Member Count",
                value="\n".join(team_list),
                inline=False,
            )

            embed.add_field(
                name="👥 Total",
                value=f"**{total_members}** total members across all clubs",
                inline=False,
            )

        if teams_not_found:
            embed.add_field(
                name="⚠️ Roles Not Found",
                value=", ".join(teams_not_found),
                inline=False,
            )

        embed.set_footer(text=f"Tracking {len(FOOTBALL_TEAMS)} football teams")

        await ctx.send(embed=embed)

    @commands.command(name="rolecount", help="Count members with a specific role")
    async def role_count(self, ctx: commands.Context, *, role_name: str) -> None:
        """
        Count members who have a specific role.
        Usage: !rolecount Role Name
        """
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role is None:
            await ctx.send(f'❌ Role "{role_name}" not found in this server.')
            return

        member_count = len(role.members)
        embed = discord.Embed(
            title="🎭 Role Count",
            description=f"**Role:** {role.mention}",
            color=role.color,
        )
        embed.add_field(name="Member Count", value=f"**{member_count}** members", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="allroles", help="List all roles and their member counts")
    async def all_roles(self, ctx: commands.Context) -> None:
        """
        Display all roles in the server with their member counts.
        Usage: !allroles
        """
        roles = [role for role in ctx.guild.roles if role.name != "@everyone"]
        roles.sort(key=lambda role: len(role.members), reverse=True)

        embed = discord.Embed(
            title=f"🗂️ Role List for {ctx.guild.name}",
            description=f"Total roles: {len(roles)}",
            color=discord.Color.blue(),
        )

        role_list = []
        for role in roles[:25]:
            member_count = len(role.members)
            role_list.append(f"{role.mention} - **{member_count}** members")

        if role_list:
            embed.add_field(
                name="Roles (sorted by member count)",
                value="\n".join(role_list),
                inline=False,
            )

        if len(roles) > 25:
            embed.set_footer(text=f"Showing top 25 of {len(roles)} roles")

        await ctx.send(embed=embed)

    @commands.command(name="multirolecount", help="Count members for multiple roles")
    async def multi_role_count(self, ctx: commands.Context, *role_names: str) -> None:
        """
        Count members for multiple roles at once.
        Usage: !multirolecount "Role 1" "Role 2" "Role 3"
        """
        if not role_names:
            await ctx.send("❌ Please provide at least one role name.")
            return

        embed = discord.Embed(
            title="🧮 Multi-Role Counts",
            description=f"Server: {ctx.guild.name}",
            color=discord.Color.green(),
        )

        for role_name in role_names:
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if role:
                member_count = len(role.members)
                embed.add_field(
                    name=role.name,
                    value=f"**{member_count}** members",
                    inline=True,
                )
            else:
                embed.add_field(
                    name=role_name,
                    value="❌ Not found",
                    inline=True,
                )

        await ctx.send(embed=embed)

    @commands.command(name="rolesearch", help="Search for roles containing a keyword")
    async def role_search(self, ctx: commands.Context, keyword: str) -> None:
        """
        Search for roles containing a specific keyword.
        Usage: !rolesearch keyword
        """
        matching_roles = [
            role
            for role in ctx.guild.roles
            if keyword.lower() in role.name.lower() and role.name != "@everyone"
        ]

        if not matching_roles:
            await ctx.send(f'❌ No roles found containing "{keyword}"')
            return

        embed = discord.Embed(
            title=f"🔎 Role Search: '{keyword}'",
            description=f"Found {len(matching_roles)} matching role(s)",
            color=discord.Color.purple(),
        )

        for role in matching_roles[:25]:
            member_count = len(role.members)
            embed.add_field(
                name=role.name,
                value=f"**{member_count}** members",
                inline=True,
            )

        await ctx.send(embed=embed)
