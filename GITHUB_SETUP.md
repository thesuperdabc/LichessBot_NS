# GitHub Actions Bot Setup

## GitHub Actions Setup

### 1. Fork Repository
Fork this repository to your GitHub account.

### 2. Add Bot Token
1. Go to your repository Settings
2. Click "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Name: `LICHESS_TOKEN`
5. Value: Your bot token (starts with `lip_`)

### 3. Enable Workflows
1. Go to "Actions" tab in your repository
2. Click "I understand my workflows, go ahead and enable them"
3. Workflows will appear automatically

### 4. Deploy Bot
**Automatic:** Push any commit to main branch
**Manual:** Actions → "Lichess Bot" → "Run workflow"

## Bot Features

- Latest Stockfish development version
- Fairy-Stockfish for variants
- Professional opening books
- 6-hour runtime cycles (24/7 operation)
- Auto-restart on schedule
- Multiple parallel instances

## Enhanced Features

- **More Chat commands** - Type `!help` in game chat to see all commands
- **Opening command** - `!opening` shows current opening name and line
- **Lower-rated bot decliner** - Automatically declines weak opponents
- **Configurable 30-second draw handling** - Set `accept_30_second_draws: true/false` in config.yml
- **Hint system** - 7-hint limit with respectful messages
- **Ping command** - `!ping` shows real network latency

## Configuration Options

### 30-Second Draw Handling
In `config.yml`, set `accept_30_second_draws`:
- `true` - Bot will accept draws in 30-second bullet games
- `false` - Bot will decline draws in 30-second bullet games

This allows users to choose their preferred strategy for bullet games.

## Monitoring

Check bot status in the Actions tab. Green = running, Red = needs restart.

## Troubleshooting

- **Bot not starting:** Check if LICHESS_TOKEN secret is added correctly
- **Workflow failed:** Click on the failed run to see error details
- **Bot stopped:** Normal after 6 hours, will restart automatically
