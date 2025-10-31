from fastapi import FastAPI
from app.routers import events, tickets, users


app = FastAPI(
    title="Tixxety API",
    description="API for managing events and ticket bookings.",
    version="1.0.0",
    contact={
        "name": "Ajayi Oluwaseyi",
        "url": "https://oluwatemmy.netlify.app",
        "email": "oluwaseyitemitope456@gmail.com"
    }
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Tixxety API"}


# Register router
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(events.router, prefix="/events", tags=["Events"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
