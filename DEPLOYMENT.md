# Deployment Guide

This guide covers deploying the Class Seat Monitor to run automatically 24/7 in the cloud.

## Table of Contents

- [GitHub Actions Deployment (Recommended)](#github-actions-deployment-recommended)
- [Alternative Deployment Options](#alternative-deployment-options)
- [Troubleshooting](#troubleshooting)

## GitHub Actions Deployment (Recommended)

GitHub Actions provides free automation that runs your bot in the cloud every 5 minutes without needing to keep a local machine running.

### Prerequisites

- GitHub account with this repository
- Telegram bot token (see main README for setup)
- Telegram chat ID(s)

### Step 1: Configure GitHub Secrets

1. Go to your repository on GitHub
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - **Name**: `TELEGRAM_BOT_TOKEN`
   - **Value**: Your Telegram bot token (from @BotFather)
5. Click **Add secret**

> **Note**: Chat IDs are configured in `config.yaml` and are not sensitive, so they don't need to be secrets.

### Step 2: Configure Monitored Courses

Edit `config.yaml` to add the courses you want to monitor:

```yaml
courses_to_monitor:
  - course_code: "CS 403"
    notify_when_seats_gt: 0
  - course_code: "HIS 362"
    notify_when_seats_gt: 0
```

Commit and push your changes:

```bash
git add config.yaml
git commit -m "Configure monitored courses"
git push
```

### Step 3: Enable GitHub Actions Workflow

The workflow is already configured in `.github/workflows/monitor.yml`. It will:
- Run automatically every 5 minutes
- Can be triggered manually
- Run in headless Chrome mode
- Send Telegram notifications when seats become available

**The workflow will start automatically once the `TELEGRAM_BOT_TOKEN` secret is configured.**

### Step 4: Verify It's Working

1. Go to the **Actions** tab in your GitHub repository
2. You should see workflow runs appearing every 5 minutes
3. Click on a run to view logs
4. Check your Telegram for notifications

### Step 5: Manual Trigger (Optional)

To run the workflow immediately:

1. Go to **Actions** tab
2. Click on **Course Seat Monitor** workflow
3. Click **Run workflow** dropdown
4. Click the green **Run workflow** button

### Monitoring and Logs

#### View Workflow Runs

1. Navigate to the **Actions** tab
2. Click on **Course Seat Monitor**
3. View the list of all workflow runs with their status

#### View Logs for a Specific Run

1. Click on any workflow run
2. Click on the **monitor** job
3. Expand any step to view detailed logs
4. Look for:
   - `Run monitoring check` - Main execution logs
   - Success/failure indicators
   - Number of courses scraped
   - Notifications sent

#### Download Logs (on Failure)

If a workflow fails, logs are automatically uploaded as artifacts:

1. Click on the failed workflow run
2. Scroll to the **Artifacts** section
3. Download **monitoring-logs**
4. Extract and review `monitor.log`

### Configuration Options

#### Change Monitoring Interval

Edit `.github/workflows/monitor.yml`:

```yaml
schedule:
  - cron: '*/10 * * * *'  # Every 10 minutes instead of 5
```

Cron syntax examples:
- `*/5 * * * *` - Every 5 minutes (default)
- `*/10 * * * *` - Every 10 minutes
- `*/15 * * * *` - Every 15 minutes
- `0 * * * *` - Every hour
- `0 */2 * * *` - Every 2 hours

> **Note**: GitHub Actions may delay scheduled workflows by a few minutes during high load.

#### Disable Automatic Monitoring

To temporarily disable automatic monitoring:

1. Go to **Actions** tab
2. Click on **Course Seat Monitor**
3. Click the **...** menu (three dots)
4. Select **Disable workflow**

To re-enable: Follow the same steps and select **Enable workflow**

### Free Tier Limits

- **2,000 minutes/month** for free GitHub accounts
- Running every 5 minutes ≈ 288 runs/day
- Each run takes ~1-2 minutes
- Total: ~288-576 minutes/day = ~8,640-17,280 minutes/month

**You'll likely exceed the free tier at 5-minute intervals.** Consider:
- Increasing interval to 10-15 minutes
- Upgrading to GitHub Pro (3,000 minutes/month)
- Using alternative deployment (see below)

### Best Practices

1. **Test locally first**: Run `python monitor_once.py` locally before deploying
2. **Monitor usage**: Check Actions usage under Settings → Billing
3. **Adjust interval**: Balance between responsiveness and cost
4. **Check logs regularly**: Ensure scraper still works (websites change!)
5. **Keep secrets secure**: Never commit tokens to git

## Alternative Deployment Options

### Option 1: Render.com (Free Tier)

Render offers free hosting for background workers:

1. Create account at [render.com](https://render.com)
2. Click **New** → **Background Worker**
3. Connect your GitHub repository
4. Configure:
   - **Name**: class-seat-monitor
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py start`
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your bot token
   - `TELEGRAM_CHAT_IDS`: Your chat IDs (comma-separated)
   - `SCRAPER_HEADLESS`: `true`
6. Deploy

**Pros**: Free, no time limits, persistent
**Cons**: Free tier can sleep after inactivity, limited resources

### Option 2: Railway.app (Free Trial)

Railway offers $5/month free credit:

1. Create account at [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repository
4. Add environment variables in Settings
5. Railway will auto-detect Python and deploy

**Pros**: Reliable, good free tier, easy setup
**Cons**: Free credit limited ($5/month), paid after trial

### Option 3: Self-Hosted (VPS)

Deploy to your own server (DigitalOcean, AWS, etc.):

1. SSH into your server
2. Clone repository
3. Install dependencies
4. Configure `.env` file
5. Set up systemd service or cron job

Example systemd service:

```ini
[Unit]
Description=Class Seat Monitor
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/class-seat-monitor
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Pros**: Full control, unlimited usage
**Cons**: Costs money, requires maintenance

### Option 4: Docker Deployment

Use the included `docker-compose.yml`:

```bash
# On your server
docker-compose up -d
```

See main README for Docker details.

## Troubleshooting

### Workflow Not Running

**Problem**: Workflow doesn't appear in Actions tab

**Solutions**:
- Ensure `.github/workflows/monitor.yml` exists in the repository
- Check that the file has correct YAML syntax
- Verify you pushed the workflow file to GitHub
- Check repository Actions permissions: Settings → Actions → General → Allow all actions

---

**Problem**: Scheduled workflow not triggering

**Solutions**:
- GitHub may delay scheduled workflows by up to 10 minutes during high load
- Scheduled workflows don't run on disabled repositories or repositories with no activity
- Try manual trigger first to ensure workflow works
- Check Actions usage limits (Settings → Billing)

### Authentication Errors

**Problem**: `Invalid bot token` or notification failures

**Solutions**:
- Verify `TELEGRAM_BOT_TOKEN` secret is set correctly (no extra spaces)
- Test bot token locally: `python main.py test-telegram`
- Regenerate bot token from @BotFather if needed
- Ensure bot has been started (send `/start` to your bot)

### Scraping Errors

**Problem**: `No courses scraped` or `Timeout waiting for course table`

**Solutions**:
- Website structure may have changed - check if website is accessible
- Verify website URL in `config.yaml` is correct
- Check if website blocks automated access
- Review scraper logs in workflow output
- Test locally in headless mode: set `headless: true` in config.yaml

---

**Problem**: ChromeDriver errors

**Solutions**:
- GitHub Actions auto-installs Chrome and ChromeDriver
- If issues persist, check workflow logs for Chrome version mismatch
- `webdriver-manager` should handle version compatibility automatically

### Performance Issues

**Problem**: Workflow runs too slowly or times out

**Solutions**:
- Increase `timeout` in scraper config (default: 30 seconds)
- Reduce number of monitored courses
- Check website response time
- Review logs for bottlenecks

---

**Problem**: Hitting GitHub Actions time limits

**Solutions**:
- Increase monitoring interval (10-15 minutes instead of 5)
- Optimize scraper performance
- Reduce number of retry attempts in scraper
- Consider alternative deployment options

### Database Issues

**Problem**: Database locked or corrupted

**Solutions**:
- GitHub Actions starts fresh each time, so database is temporary
- For persistent monitoring history, use alternative deployment
- Database is recreated on each workflow run (by design)

### Notification Issues

**Problem**: Not receiving notifications

**Solutions**:
- Verify chat ID in `config.yaml` is correct
- Test Telegram locally: `python main.py test-telegram`
- Check if bot was blocked or removed from chat
- Review notification logs in workflow output
- Ensure threshold is set correctly (notify_when_seats_gt)

---

**Problem**: Too many notifications

**Solutions**:
- Increase `notify_when_seats_gt` threshold
- Reduce monitoring frequency
- Add cooldown logic (requires code changes)

### General Debugging

1. **Check workflow logs**:
   - Actions tab → Click on run → Click on job → Expand steps

2. **Download logs** (if workflow failed):
   - Scroll to Artifacts section → Download monitoring-logs

3. **Test locally first**:
   ```bash
   python monitor_once.py
   ```

4. **Test Telegram**:
   ```bash
   python main.py test-telegram
   ```

5. **Test scraper**:
   ```bash
   python main.py test-scraper
   ```

6. **Check GitHub status**:
   - Visit [githubstatus.com](https://www.githubstatus.com) for service issues

### Getting Help

If issues persist:

1. Check existing GitHub issues
2. Create new issue with:
   - Workflow logs
   - Configuration (remove sensitive data)
   - Error messages
   - Steps to reproduce
3. Include monitoring logs if available

## Security Notes

- **Never commit** `.env` files or secrets to git
- Use GitHub Secrets for sensitive data
- Rotate bot token periodically
- Review workflow logs for exposed credentials
- Use environment variables for configuration

## Updates and Maintenance

### Updating the Bot

1. Pull latest changes from repository
2. Review changelog for breaking changes
3. Update configuration if needed
4. Test locally before deploying
5. Push changes to GitHub (workflow auto-updates)

### Monitoring Health

- Check Actions tab regularly
- Review notification patterns
- Verify scraper still works (websites change!)
- Monitor GitHub Actions usage
- Test after long periods of inactivity

### Handling Website Changes

If the target website changes structure:

1. Scraper may stop working
2. Check workflow logs for errors
3. Update scraper selectors in `src/scraper.py`
4. Test locally before deploying
5. Create issue or PR with fixes

---

## Summary

**GitHub Actions** is recommended for:
- ✅ Easy setup
- ✅ No server maintenance
- ✅ Integrated with GitHub
- ✅ Free (with limits)
- ❌ Usage limits
- ❌ Temporary database

**Alternative hosting** is recommended for:
- ✅ Persistent database
- ✅ More control
- ✅ Higher reliability
- ❌ Costs money
- ❌ Requires setup

Choose based on your needs and budget!
