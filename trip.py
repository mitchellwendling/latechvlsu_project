"""Static trip configuration. Single source of truth for the dashboard."""

TRIP = {
    "name": "Kentucky @ Oklahoma",
    "game_date": "2026-10-17",
    "kickoff_note": "Time TBA (SEC home games commonly 11:00 AM, 2:30, or 6:00 PM CT)",
    "venue": "Gaylord Family Oklahoma Memorial Stadium, Norman, OK",
    "origin_airport": "CVG",
    "destination_airport": "DFW",
    "depart_date": "2026-10-16",
    "return_date": "2026-10-18",
    "travelers": 1,
}

TICKET_SOURCES = [
    {
        "name": "SeatGeek",
        "url": "https://seatgeek.com/search?search=Oklahoma+Kentucky+October+17",
        "search_url": "https://seatgeek.com/search?search=Oklahoma+Kentucky+October+17",
    },
    {
        "name": "StubHub",
        "url": "https://www.stubhub.com/oklahoma-sooners-football-tickets",
        "search_url": "https://www.stubhub.com/find/s/?q=Oklahoma+Kentucky",
    },
    {
        "name": "Vivid Seats",
        "url": "https://www.vividseats.com/oklahoma-sooners-football-tickets--sports-ncaa-football.html",
        "search_url": "https://www.vividseats.com/search?searchTerm=Oklahoma+Kentucky",
    },
    {
        "name": "OU Official (Ticketmaster)",
        "url": "https://soonersports.com/sports/football/tickets",
        "search_url": "https://www.ticketmaster.com/oklahoma-sooners-football-tickets/artist/805962",
    },
]
