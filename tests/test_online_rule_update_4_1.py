from scripts.online_rule_update import valid_candidate, service_for


def test_valid_domain_and_cidr():
    assert valid_candidate("apple.com")
    assert valid_candidate("17.0.0.0/8")
    assert valid_candidate("2403:300::/32")


def test_reject_url():
    assert not valid_candidate("https://apple.com/path")


def test_apple_classification():
    assert service_for("apple", "account.apple.com") == "apple-account"
    assert service_for("apple", "setup.icloud.com") == "icloud"
    assert service_for("apple", "music.apple.com") == "apple-music"


def test_google_classification():
    assert service_for("google", "play.googleapis.com") == "google-play"
    assert service_for("google", "fcm.googleapis.com") == "fcm"
    assert service_for("google", "gmail.com") == "gmail"
