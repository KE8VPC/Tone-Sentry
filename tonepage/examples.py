def integration_examples():
    return {
        "instructions": "Copy entries into integrations in Settings. Configure endpoint and environment variables, then explicitly enable. Default trigger is recording_complete. Tone sharing is controlled separately per tone set.",
        "weekly_test_example": {"timezone": "America/New_York", "days": [0], "start": "18:00", "minutes": 5, "mode": "record_only"},
        "integrations": [
            {"id": "dispatch-webhook", "kind": "webhook", "enabled": False, "scope": "shared",
             "url": "https://your-server.example/dispatch", "token_env": "DISPATCH_WEBHOOK_TOKEN",
             "hmac_env": "DISPATCH_WEBHOOK_SIGNING_KEY", "triggers": ["activation", "recording_complete", "transcript_complete"],
             "tone_ids": [], "include_transcript": False},
            {"id": "audio-archive", "kind": "ftps", "enabled": False, "scope": "shared",
             "host": "ftp.your-server.example", "port": 21, "username": "receiver",
             "password_env": "TONEPAGE_FTP_PASSWORD", "directory": "/dispatch", "protect_recording": True},
            {"id": "transcribe", "kind": "transcription", "enabled": False, "scope": "shared",
             "url": "https://your-provider.example/transcribe", "token_env": "TRANSCRIPTION_API_KEY",
             "file_field": "file", "text_field": "text", "fields": {"model": "your-model"},
             "daily_limit": 100, "max_bytes": 25000000, "protect_recording": True},
            {"id": "local-script", "kind": "script", "enabled": False, "scope": "local",
             "argv": ["python", "/absolute/path/your_script.py", "{recording_id}", "{path}"],
             "triggers": ["recording_complete"], "timeout": 30},
        ],
    }

