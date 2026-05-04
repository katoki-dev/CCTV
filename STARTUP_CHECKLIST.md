# CEMSS System Startup Checklist

## Pre-Startup Checks

- [ ] Verify Ollama is running (`http://localhost:11434`)
- [ ] Check required models installed:
  - [ ] `ollama list` shows llama3.2:3b (or configured LLM model)
  - [ ] `ollama list` shows moondream (for VLM verification)
  - [ ] `ollama list` shows cemss-threat-scanner (for tier-1 VLM)
- [ ] Database exists (if not, will be created on first run)
- [ ] Configuration files present (config.py, .env)

## Startup Tests

### 1. Database Initialization

```bash
# If database doesn't exist yet, it will be created on first app run
python start.py
# Stop after database is created
# Then run learning tables setup
python utils/update_database_learning.py
```

### 2. Check Startup Logs

Look for these messages when starting:

- ✓ Loaded detection models: [list of models]
- ✓ Pose estimator loaded for skeletal tracking
- ✓ LLM Video Analyzer loaded
- ✓ Continuous Analysis Manager initialized
- ✓ Self-Learning System initialized (autonomous VLM verification)
- VLM Verification worker started

### 3. Test Detection

- [ ] Add test camera or video file
- [ ] Enable detection for test camera
- [ ] Verify detections occur
- [ ] Check for random sampling messages: "→ Sampled [model] detection for learning"

### 4. Test VLM Verification

- [ ] Wait 60 seconds for verification worker cycle
- [ ] Check logs for: "Processing X detection verifications..."
- [ ] Verify verifications stored in database

### 5. Database Verification

```sql
-- Check if learning tables exist
SELECT name FROM sqlite_master WHERE type='table';

-- Check sampled verifications
SELECT COUNT(*) FROM verification_logs;

-- Check performance tracking
SELECT * FROM model_performance ORDER BY date DESC;

-- Check training queue
SELECT * FROM training_queue;
```

## Expected System Behavior

### Random Sampling (5% Rate)

- Out of every 100 detections, ~5 should be sampled
- Sampled frames saved to: `learning_data/verification_images/`
- Console message: "→ Sampled [model_name] detection for learning"

### VLM Verification Worker (Every 60s)

- Processes up to 5 verifications per cycle
- Logs: "Processing X detection verifications..."
- Logs: "VLM verification batch complete: X/Y successful"

### Performance Tracking

- Daily metrics updated in `model_performance` table
- Tracks accuracy based on VLM verifications
- Calculates true positives vs false positives

### Retraining Queue

- When 200+ verified samples collected
- Model automatically queued for retraining
- Entry in `training_queue` with status=PENDING

## Troubleshooting

### "Self-Learning System disabled"

- Check `LEARNING_ENABLED=True` in config.py
- Check `RANDOM_SAMPLING_ENABLED=True`

### "VLM Verification worker" not starting

- Verify learning system initialized first
- Check VLM model installed: `ollama list | grep moondream`

### No sampling occurring

- Verify detections are happening
- Check `SAMPLING_RATE` > 0 in config
- Check `learning_data/verification_images/` directory exists

### VLM verification failing

- Test VLM directly: `ollama run moondream`
- Check `VLM_VERIFICATION_MODEL` matches installed model
- Verify timeout settings (default 15s)

### Database errors

- Ensure database.db exists
- Run: `python utils/update_database_learning.py`
- Check file permissions on learning_data/ directory

## Success Criteria

✓ System starts without errors
✓ All components initialize (detectors, LLM, VLM, learning system)
✓ Detections occur and are logged
✓ Random sampling works (~5% of detections)
✓ VLM verification worker processes queue
✓ Verifications stored in database
✓ Performance metrics updated

## Quick Start Commands

```bash
# 1. Start CEMSS
cd c:/Users/anina/OneDrive/Desktop/Project/CEMSS/v11.2
python start.py

# 2. In another terminal - Setup learning tables (if not done)
python utils/update_database_learning.py

# 3. Monitor logs
# Watch for learning system messages in console

# 4. Check database
sqlite3 database.db "SELECT COUNT(*) FROM verification_logs;"

# 5. Test VLM
python test_quick_integration.py
```

## Notes

- First startup creates database (may take a few seconds)
- Learning directories created automatically
- VLM verification is asynchronous (runs in background)
- No detections will be sampled until detection is enabled on a camera
- Retraining service implementation is optional (not yet implemented)
