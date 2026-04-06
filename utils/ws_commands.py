WS_CMD = {
    "INVITATION": "305",
    "SUBSCRIBE": "16000",
    "JOIN_ROOM": "16012",
    "BET_START": "16005",
    "PLACE_BET": "16002",
    "WALLET_BEFORE": "100",
    "WALLET_UPDATE": "317",
    "END_GAME" : "16006",
    "CHAT" : "16008",
    "REBET" : "16010",
    "LEAVE_ROOM" : "16013",
    "UNSUBSCRIBE": "16001",
    
}


# Popup-related/global modal commands
POPUP_CMDS = {
    "JOIN_TABLE_INVITATION": "305",
    "MESSAGES_AND_NEWS": "104",
    "PROMOTION_MESSAGE": "6",
    "FREE_GIFTCARD": "8",
    "BROADCAST_MESSAGE": "10",
    "SHOW_WEBVIEW": "12",
    "LOAN_MESSAGE": "322",
    "VERIFY_PHONE_NUMBER": "103",
}

# Optional quick set for checks
POPUP_CMD_VALUES = set(POPUP_CMDS.values())