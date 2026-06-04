import os
from datetime import datetime

import discord
from discord.ext import commands

from config import COMPETITIONS, FOOTBALL_DATA_BASE_URL
from helpers import _fetch_football_data, _format_kickoff, _parse_utc_date, _role_for_team
from predictions_store import (
    load_predictions,
    outcome_from_score,
    record_prediction,
    save_predictions,
    score_prediction,
)


class PredictionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _resolve_user_display(self, ctx: commands.Context, user_id: str) -> tuple[str, discord.abc.User | None]:
        user_int = int(user_id)
        member = None
        if ctx.guild:
            member = ctx.guild.get_member(user_int)
            if member is None:
                try:
                    member = await ctx.guild.fetch_member(user_int)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    member = None

        if member:
            return member.display_name, member

        try:
            user = await self.bot.fetch_user(user_int)
        except discord.HTTPException:
            return f"User {user_id}", None

        return user.display_name, user

    @commands.command(name="predict", aliases=["plpredict"], help="Predict a match outcome")
    async def predict_match(self, ctx: commands.Context, match_id: int, *prediction: str) -> None:
        """
        Predict a match outcome.
        Usage: !predict <match_id> <home|away|draw>
        """
        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            await ctx.send("❌ FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
            return

        if not prediction:
            await ctx.send("❌ Please provide a prediction: home, away, or draw.")
            return

        if len(prediction) == 1:
            raw = prediction[0].strip().lower()
            if raw in {"home", "h", "1"}:
                outcome = "HOME"
            elif raw in {"away", "a", "2"}:
                outcome = "AWAY"
            elif raw in {"draw", "d", "x"}:
                outcome = "DRAW"
            else:
                await ctx.send("❌ Prediction must be `home`, `away`, or `draw`.")
                return
        elif len(prediction) == 2 and all(item.isdigit() for item in prediction):
            await ctx.send("❌ Scoreline predictions are disabled. Use `home`, `away`, or `draw`.")
            return
        else:
            await ctx.send("❌ Prediction must be `home`, `away`, or `draw`.")
            return

        try:
            match_payload = await _fetch_football_data(
                f"{FOOTBALL_DATA_BASE_URL}/matches/{match_id}",
                token,
            )
        except Exception as exc:
            await ctx.send(f"❌ Football API error: {exc}")
            return

        match = match_payload.get("match")
        if not match and match_payload.get("id"):
            match = match_payload
        if not match:
            await ctx.send("❌ Match not found.")
            return

        status = match.get("status")
        if status == "FINISHED":
            await ctx.send("❌ That match is already finished. Predictions must be made before kickoff.")
            return

        data = load_predictions()
        record_prediction(data, match_id, ctx.author.id, outcome)
        save_predictions(data)

        home_name = match["homeTeam"]["name"]
        away_name = match["awayTeam"]["name"]
        home_role = _role_for_team(ctx.guild, home_name) if ctx.guild else None
        away_role = _role_for_team(ctx.guild, away_name) if ctx.guild else None
        home_display = home_role.mention if home_role else home_name
        away_display = away_role.mention if away_role else away_name

        if outcome == "HOME":
            outcome_text = f"{home_display} to win"
        elif outcome == "AWAY":
            outcome_text = f"{away_display} to win"
        else:
            outcome_text = "draw"

        await ctx.send(
            f"✅ Prediction saved for match `{match_id}`: {outcome_text}",
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

    @commands.command(name="mypicks", aliases=["plmypicks", "plpicks"], help="Show your predictions")
    async def my_picks(self, ctx: commands.Context) -> None:
        """
        Show the user's predictions.
        Usage: !mypicks
        """
        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            await ctx.send("❌ FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
            return

        data = load_predictions()
        predictions = data.get("predictions", {})
        user_id = str(ctx.author.id)
        picks = []

        for match_id, match_bucket in predictions.items():
            prediction = match_bucket.get("predictions", {}).get(user_id)
            if prediction:
                picks.append((match_id, prediction))

        if not picks:
            await ctx.send("❌ You have no predictions yet. Use `!predict` to add one.")
            return

        entries = []
        errors = 0
        for match_id, prediction in picks:
            try:
                match_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/matches/{match_id}",
                    token,
                )
            except Exception:
                errors += 1
                match_payload = {}

            match = match_payload.get("match")
            if not match and match_payload.get("id"):
                match = match_payload

            if match:
                home_name = match["homeTeam"]["name"]
                away_name = match["awayTeam"]["name"]
                kickoff = _parse_utc_date(match.get("utcDate"))
                status = match.get("status", "SCHEDULED")
                competition = match.get("competition", {})
                competition_name = COMPETITIONS.get(
                    competition.get("code"),
                    competition.get("name", "Unknown League"),
                )
                if status == "FINISHED":
                    score = match.get("score", {}).get("fullTime", {})
                    actual_home = score.get("home")
                    actual_away = score.get("away")
                    if actual_home is not None and actual_away is not None:
                        status_text = f"Result: {actual_home}-{actual_away}"
                    else:
                        status_text = "Result: Final"
                else:
                    kickoff_text = _format_kickoff(match.get("utcDate"))
                    status_text = f"Kickoff {kickoff_text}" if kickoff_text else f"Status: {status}"
            else:
                home_name = "Match data"
                away_name = "unavailable"
                kickoff = None
                status_text = "Status: Unknown"
                competition_name = "Unknown League"

            pred_home = prediction.get("home")
            pred_away = prediction.get("away")
            predicted = prediction.get("outcome")
            if pred_home is not None and pred_away is not None:
                prediction_text = f"Prediction: {pred_home}-{pred_away}"
            elif predicted == "HOME":
                prediction_text = "Prediction: Home win"
            elif predicted == "AWAY":
                prediction_text = "Prediction: Away win"
            elif predicted == "DRAW":
                prediction_text = "Prediction: Draw"
            else:
                prediction_text = "Prediction: Unknown"

            entries.append(
                (
                    kickoff or datetime.max,
                    match_id,
                    f"{home_name} vs {away_name}\nLeague: {competition_name}\n{prediction_text}\n{status_text}",
                )
            )

        entries.sort(key=lambda item: item[0])

        embed = discord.Embed(
            title="🧾 Your Picks",
            description=f"Total picks: {len(entries)}",
            color=discord.Color.blurple(),
        )

        for _, match_id, value in entries[:20]:
            embed.add_field(name=f"Match {match_id}", value=value, inline=False)

        if len(entries) > 20:
            embed.set_footer(text=f"Showing 20 of {len(entries)} picks.")
        elif errors:
            embed.set_footer(text=f"{errors} match(es) could not be loaded.")

        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["plleaderboard"], help="Show prediction leaderboard")
    async def leaderboard(self, ctx: commands.Context) -> None:
        """
        Show prediction leaderboard for completed matches.
        Usage: !leaderboard
        """
        token = os.getenv("FOOTBALL_DATA_TOKEN")
        if not token:
            await ctx.send("❌ FOOTBALL_DATA_TOKEN is not set. Add it to your .env file.")
            return

        data = load_predictions()
        predictions = data.get("predictions", {})
        if not predictions:
            await ctx.send("❌ No predictions found yet. Use `!predict` to add one.")
            return

        points: dict[str, int] = {}
        scored: dict[str, int] = {}
        finished_matches = 0
        errors = 0

        for match_id, match_bucket in predictions.items():
            match_predictions = match_bucket.get("predictions", {})
            if not match_predictions:
                continue

            try:
                match_payload = await _fetch_football_data(
                    f"{FOOTBALL_DATA_BASE_URL}/matches/{match_id}",
                    token,
                )
            except Exception:
                errors += 1
                continue

            match = match_payload.get("match")
            if not match and match_payload.get("id"):
                match = match_payload
            if not match or match.get("status") != "FINISHED":
                continue

            score = match.get("score", {}).get("fullTime", {})
            actual_home = score.get("home")
            actual_away = score.get("away")
            if actual_home is None or actual_away is None:
                continue

            finished_matches += 1
            for user_id, prediction in match_predictions.items():
                predicted = prediction.get("outcome")
                pred_home = prediction.get("home")
                pred_away = prediction.get("away")
                if not predicted and pred_home is not None and pred_away is not None:
                    predicted = outcome_from_score(pred_home, pred_away)

                if not predicted:
                    continue

                earned = score_prediction(predicted, actual_home, actual_away)
                points[user_id] = points.get(user_id, 0) + earned
                scored[user_id] = scored.get(user_id, 0) + 1

        if not points:
            await ctx.send("❌ No completed matches have been scored yet.")
            return

        leaderboard = sorted(points.items(), key=lambda item: (-item[1], item[0]))
        embed = discord.Embed(
            title="🏅 Prediction Leaderboard",
            description=f"Scored matches: {finished_matches} (2 pts per correct outcome)",
            color=discord.Color.teal(),
        )

        for idx, (user_id, total_points) in enumerate(leaderboard[:10], 1):
            display, _ = await self._resolve_user_display(ctx, user_id)
            played = scored.get(user_id, 0)
            embed.add_field(
                name=f"{idx}. {display}",
                value=f"**{total_points}** points in {played} match(es)",
                inline=False,
            )

        if errors:
            embed.set_footer(text=f"{errors} match(es) could not be scored due to API errors.")

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
