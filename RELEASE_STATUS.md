# v1.0.0 Release Status

**Code & configs: READY**  
**Git tag `v1.0.0`: NOT YET PUSHED** (GitHub App has no create-tag permission)

## Daddy, run this once:

```bash
cd Proxy-Config-Center
git pull origin main
bash scripts/release.sh 1.0.0
```

Or only the tag:

```bash
git pull origin main
git tag v1.0.0
git push origin v1.0.0
```

After the tag is pushed, Actions will publish the GitHub Release automatically.

## Verified locally
- validate / semantic / golden / build / check_config — all passed
- 6 platform outputs generated
