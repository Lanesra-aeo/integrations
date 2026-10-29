# GitHub Actions

[`weekly-visibility-report.yml`](weekly-visibility-report.yml) runs [`weekly_report.py`](../python/weekly_report.py) every Monday and posts the result to Slack. The steps to set it up in your own repository are at the top of the file.

The same pattern runs [`visibility_alert.py`](../python/visibility_alert.py) daily: schedule it after your project's daily capture, and the job fails, which GitHub can email you about, when visibility drops.

Give the workflow a key of its own, so revoking it never breaks anything else. A Viewer key is enough: these scripts only read.
