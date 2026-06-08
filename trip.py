"""Static trip configuration. Single source of truth for the dashboard."""

TRIP = {
    "name": "LA Tech @ LSU",
    "game_date": "2026-09-12",
    "kickoff_note": "Time TBA (typical LSU home: 6:30 or 7:00 PM CT)",
    "venue": "Tiger Stadium, Baton Rouge, LA",
    "origin_airport": "CVG",
    "destination_airport": "BTR",
    "depart_date": "2026-09-11",
    "return_date": "2026-09-13",
    "travelers": 1,
}

TICKET_SOURCES = [
    {
        "name": "SeatGeek",
        "url": "https://seatgeek.com/lsu-tigers-football-vs-louisiana-tech-bulldogs-tickets/2026-09-12-6-pm/college-football/6618000",
        "search_url": "https://seatgeek.com/search?search=LSU+Louisiana+Tech+September+12",
    },
    {
        "name": "StubHub",
        "url": "https://www.stubhub.com/lsu-tigers-football-tickets",
        "search_url": "https://www.stubhub.com/find/s/?q=LSU+Louisiana+Tech",
    },
    {
        "name": "Vivid Seats",
        "url": "https://www.vividseats.com/lsu-tigers-football-tickets--sports-ncaa-football.html",
        "search_url": "https://www.vividseats.com/search?searchTerm=LSU+Louisiana+Tech",
    },
    {
        "name": "LSU Official (Ticketmaster)",
        "url": "https://lsusports.net/sports/football/tickets/",
        "search_url": "https://www.ticketmaster.com/lsu-tigers-football-tickets/artist/805976",
    },
]
