from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(
    title="SpeedRide Car Rental Service",
    description="Complete Car Rental backend — All 20 tasks (Day 1–6)",
    version="1.0.0"
)

# ─────────────────────────────────────────────
# In-memory Data Store
# ─────────────────────────────────────────────

cars = [
    {"id": 1, "model": "Swift",    "brand": "Maruti",  "type": "Hatchback", "price_per_day": 1200, "fuel_type": "Petrol",   "is_available": True},
    {"id": 2, "model": "City",     "brand": "Honda",   "type": "Sedan",     "price_per_day": 1800, "fuel_type": "Petrol",   "is_available": True},
    {"id": 3, "model": "Creta",    "brand": "Hyundai", "type": "SUV",       "price_per_day": 2500, "fuel_type": "Diesel",   "is_available": True},
    {"id": 4, "model": "Fortuner", "brand": "Toyota",  "type": "SUV",       "price_per_day": 4000, "fuel_type": "Diesel",   "is_available": False},
    {"id": 5, "model": "Model 3",  "brand": "Tesla",   "type": "Luxury",    "price_per_day": 6000, "fuel_type": "Electric", "is_available": True},
    {"id": 6, "model": "Nexon EV", "brand": "Tata",    "type": "Hatchback", "price_per_day": 1500, "fuel_type": "Electric", "is_available": True},
    {"id": 7, "model": "3 Series", "brand": "BMW",     "type": "Luxury",    "price_per_day": 7000, "fuel_type": "Petrol",   "is_available": True},
    {"id": 8, "model": "Innova",   "brand": "Toyota",  "type": "Sedan",     "price_per_day": 2200, "fuel_type": "Diesel",   "is_available": False},
]

rentals = []
rental_counter = 1
car_counter = 9


# ─────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────

# Q6 + Q9 — RentalRequest
class RentalRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    car_id: int = Field(..., gt=0)
    days: int = Field(..., gt=0, le=30)
    license_number: str = Field(..., min_length=8)
    insurance: bool = False
    driver_required: bool = False  # Q9 addition

# Q11 — NewCar
class NewCar(BaseModel):
    model: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=2)
    type: str = Field(..., min_length=2)
    price_per_day: int = Field(..., gt=0)
    fuel_type: str = Field(..., min_length=2)
    is_available: bool = True


# ─────────────────────────────────────────────
# Helper Functions (Day 3)
# ─────────────────────────────────────────────

# Q7 — find_car
def find_car(car_id: int):
    for car in cars:
        if car["id"] == car_id:
            return car
    return None

# Q7 + Q9 — calculate_rental_cost with full breakdown
def calculate_rental_cost(price_per_day: int, days: int, insurance: bool, driver_required: bool):
    base_cost = price_per_day * days

    if days >= 15:
        discount_pct = 25
    elif days >= 7:
        discount_pct = 15
    else:
        discount_pct = 0

    discount_amount = round(base_cost * discount_pct / 100)
    after_discount = base_cost - discount_amount
    insurance_cost = 500 * days if insurance else 0
    driver_cost = 800 * days if driver_required else 0
    total_cost = after_discount + insurance_cost + driver_cost

    return {
        "base_cost": base_cost,
        "discount_percent": discount_pct,
        "discount_amount": discount_amount,
        "after_discount": after_discount,
        "insurance_cost": insurance_cost,
        "driver_cost": driver_cost,
        "total_cost": total_cost
    }

# Q10 — filter_cars_logic
def filter_cars_logic(type=None, brand=None, fuel_type=None, max_price=None, is_available=None):
    result = cars[:]
    if type is not None:
        result = [c for c in result if c["type"].lower() == type.lower()]
    if brand is not None:
        result = [c for c in result if c["brand"].lower() == brand.lower()]
    if fuel_type is not None:
        result = [c for c in result if c["fuel_type"].lower() == fuel_type.lower()]
    if max_price is not None:
        result = [c for c in result if c["price_per_day"] <= max_price]
    if is_available is not None:
        result = [c for c in result if c["is_available"] == is_available]
    return result


# ═══════════════════════════════════════════════
# IMPORTANT: All fixed /cars/... routes MUST come
# BEFORE the variable /cars/{car_id} route!
# ═══════════════════════════════════════════════

# Q1 — Home Route
@app.get("/", tags=["General"])
def home():
    return {"message": "Welcome to SpeedRide Car Rentals"}


# ── FIXED /cars ROUTES (Q2, Q5, Q10, Q15, Q16, Q17, Q18, Q20) ──

# Q2 — List all cars
@app.get("/cars", tags=["Cars"])
def get_all_cars():
    available_count = sum(1 for c in cars if c["is_available"])
    return {"total": len(cars), "available_count": available_count, "cars": cars}

# Q5 — Summary (fixed, must be above /cars/{car_id})
@app.get("/cars/summary", tags=["Cars"])
def cars_summary():
    total = len(cars)
    available = sum(1 for c in cars if c["is_available"])
    type_breakdown = {}
    fuel_breakdown = {}
    for c in cars:
        type_breakdown[c["type"]] = type_breakdown.get(c["type"], 0) + 1
        fuel_breakdown[c["fuel_type"]] = fuel_breakdown.get(c["fuel_type"], 0) + 1
    cheapest = min(cars, key=lambda c: c["price_per_day"])
    expensive = max(cars, key=lambda c: c["price_per_day"])
    return {
        "total_cars": total,
        "available_count": available,
        "breakdown_by_type": type_breakdown,
        "breakdown_by_fuel_type": fuel_breakdown,
        "cheapest_car_per_day": {"model": cheapest["model"], "brand": cheapest["brand"], "price_per_day": cheapest["price_per_day"]},
        "most_expensive_car_per_day": {"model": expensive["model"], "brand": expensive["brand"], "price_per_day": expensive["price_per_day"]}
    }

# Q10 — Filter (fixed, must be above /cars/{car_id})
@app.get("/cars/filter", tags=["Cars"])
def filter_cars_endpoint(
    type: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    max_price: Optional[int] = Query(None, gt=0),
    is_available: Optional[bool] = Query(None)
):
    result = filter_cars_logic(type, brand, fuel_type, max_price, is_available)
    if not result:
        raise HTTPException(status_code=404, detail="No cars match the given filters")
    return {"total": len(result), "cars": result}

# Q15 — Unavailable cars (fixed, must be above /cars/{car_id})
@app.get("/cars/unavailable", tags=["Cars"])
def get_unavailable_cars():
    result = [c for c in cars if not c["is_available"]]
    return {"total": len(result), "cars": result}

# Q16 — Keyword search (fixed, must be above /cars/{car_id})
@app.get("/cars/search", tags=["Advanced"])
def search_cars(keyword: str = Query(..., min_length=1)):
    kw = keyword.lower()
    result = [
        c for c in cars
        if kw in c["model"].lower()
        or kw in c["brand"].lower()
        or kw in c["type"].lower()
    ]
    if not result:
        return {"keyword": keyword, "total_found": 0, "message": f"No cars found matching '{keyword}'", "cars": []}
    return {"keyword": keyword, "total_found": len(result), "cars": result}

# Q17 — Sort (fixed, must be above /cars/{car_id})
@app.get("/cars/sort", tags=["Advanced"])
def sort_cars(
    sort_by: str = Query("price_per_day", description="price_per_day | brand | type"),
    order: str = Query("asc", description="asc | desc")
):
    valid_fields = ["price_per_day", "brand", "type"]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_fields}")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
    result = sorted(cars, key=lambda c: c[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "total": len(result), "cars": result}

# Q18 — Pagination (fixed, must be above /cars/{car_id})
@app.get("/cars/page", tags=["Advanced"])
def paginate_cars(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20)
):
    total = len(cars)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    paginated = cars[start:start + limit]
    return {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "cars": paginated}

# Q20 — Combined Browse (fixed, must be above /cars/{car_id})
@app.get("/cars/browse", tags=["Advanced"])
def browse_cars(
    keyword: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    max_price: Optional[int] = Query(None, gt=0),
    is_available: Optional[bool] = Query(None),
    sort_by: str = Query("price_per_day", description="price_per_day | brand | type"),
    order: str = Query("asc", description="asc | desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20)
):
    result = cars[:]
    # 1. Keyword search
    if keyword is not None:
        kw = keyword.lower()
        result = [c for c in result if kw in c["model"].lower() or kw in c["brand"].lower() or kw in c["type"].lower()]
    # 2. Filters
    if type is not None:
        result = [c for c in result if c["type"].lower() == type.lower()]
    if fuel_type is not None:
        result = [c for c in result if c["fuel_type"].lower() == fuel_type.lower()]
    if max_price is not None:
        result = [c for c in result if c["price_per_day"] <= max_price]
    if is_available is not None:
        result = [c for c in result if c["is_available"] == is_available]
    # 3. Sort
    valid_fields = ["price_per_day", "brand", "type"]
    if sort_by in valid_fields:
        result = sorted(result, key=lambda c: c[sort_by], reverse=(order == "desc"))
    # 4. Paginate
    total = len(result)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    paginated = result[start:start + limit]
    return {
        "total_results": total, "page": page, "limit": limit,
        "total_pages": total_pages, "sort_by": sort_by, "order": order,
        "cars": paginated
    }

# Q11 — POST /cars (Add new car — 201)
@app.post("/cars", status_code=201, tags=["Cars"])
def add_car(new_car: NewCar):
    global car_counter
    for c in cars:
        if c["model"].lower() == new_car.model.lower() and c["brand"].lower() == new_car.brand.lower():
            raise HTTPException(status_code=400, detail=f"Car '{new_car.brand} {new_car.model}' already exists")
    car = {"id": car_counter, **new_car.dict()}
    cars.append(car)
    car_counter += 1
    return {"message": "Car added successfully", "car": car}

# Q12 — PUT /cars/{car_id}
@app.put("/cars/{car_id}", tags=["Cars"])
def update_car(
    car_id: int,
    price_per_day: Optional[int] = Query(None, gt=0),
    is_available: Optional[bool] = Query(None)
):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail=f"Car {car_id} not found")
    if price_per_day is not None:
        car["price_per_day"] = price_per_day
    if is_available is not None:
        car["is_available"] = is_available
    return {"message": "Car updated successfully", "car": car}

# Q13 — DELETE /cars/{car_id}
@app.delete("/cars/{car_id}", tags=["Cars"])
def delete_car(car_id: int):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail=f"Car {car_id} not found")
    for r in rentals:
        if r["car_id"] == car_id and r["status"] == "active":
            raise HTTPException(status_code=400, detail="Cannot delete a car with an active rental")
    cars.remove(car)
    return {"message": f"Car {car_id} deleted successfully"}

# Q3 — Get car by ID  ← VARIABLE ROUTE, must be LAST among /cars/... routes
@app.get("/cars/{car_id}", tags=["Cars"])
def get_car_by_id(car_id: int):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail=f"Car {car_id} not found")
    return car


# ═══════════════════════════════════════════════
# RENTALS — fixed routes first, variable last
# ═══════════════════════════════════════════════

# Q4 — Get all rentals
@app.get("/rentals", tags=["Rentals"])
def get_all_rentals():
    return {"total": len(rentals), "rentals": rentals}

# Q15 — Active rentals (fixed)
@app.get("/rentals/active", tags=["Rentals"])
def get_active_rentals():
    active = [r for r in rentals if r["status"] == "active"]
    return {"total": len(active), "rentals": active}

# Q19 — Search rentals by customer_name (fixed)
@app.get("/rentals/search", tags=["Advanced"])
def search_rentals(customer_name: str = Query(..., min_length=1)):
    result = [r for r in rentals if customer_name.lower() in r["customer_name"].lower()]
    if not result:
        return {"customer_name": customer_name, "total_found": 0, "message": "No rentals found", "rentals": []}
    return {"customer_name": customer_name, "total_found": len(result), "rentals": result}

# Q19 — Sort rentals (fixed)
@app.get("/rentals/sort", tags=["Advanced"])
def sort_rentals(
    sort_by: str = Query("total_cost", description="total_cost | days"),
    order: str = Query("asc", description="asc | desc")
):
    valid_fields = ["total_cost", "days"]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_fields}")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
    result = sorted(rentals, key=lambda r: r[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "total": len(result), "rentals": result}

# Q19 — Paginate rentals (fixed)
@app.get("/rentals/page", tags=["Advanced"])
def paginate_rentals(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20)
):
    total = len(rentals)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    paginated = rentals[start:start + limit]
    return {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "rentals": paginated}

# Q15 — Rentals by car ID (fixed prefix)
@app.get("/rentals/by-car/{car_id}", tags=["Rentals"])
def rentals_by_car(car_id: int):
    result = [r for r in rentals if r["car_id"] == car_id]
    return {"car_id": car_id, "total": len(result), "rentals": result}

# Q14 — Get rental by ID  ← VARIABLE ROUTE, must be LAST among /rentals/... routes
@app.get("/rentals/{rental_id}", tags=["Rentals"])
def get_rental_by_id(rental_id: int):
    for r in rentals:
        if r["rental_id"] == rental_id:
            return r
    raise HTTPException(status_code=404, detail=f"Rental {rental_id} not found")

# Q8 + Q9 — POST /rentals (Create rental, 201)
@app.post("/rentals", status_code=201, tags=["Rentals"])
def create_rental(req: RentalRequest):
    global rental_counter
    car = find_car(req.car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if not car["is_available"]:
        raise HTTPException(status_code=400, detail="Car is not available for rental")

    cost = calculate_rental_cost(car["price_per_day"], req.days, req.insurance, req.driver_required)

    rental = {
        "rental_id": rental_counter,
        "customer_name": req.customer_name,
        "license_number": req.license_number,
        "car_id": req.car_id,
        "car_model": car["model"],
        "car_brand": car["brand"],
        "days": req.days,
        "insurance": req.insurance,
        "driver_required": req.driver_required,
        "status": "active",
        **cost
    }

    car["is_available"] = False
    rentals.append(rental)
    rental_counter += 1
    return {"message": "Rental created successfully", "rental": rental}


# ═══════════════════════════════════════════════
# DAY 5 — Return Workflow (Q14)
# ═══════════════════════════════════════════════

# Q14 — Return car
@app.post("/return/{rental_id}", tags=["Workflow"])
def return_car(rental_id: int):
    rental = None
    for r in rentals:
        if r["rental_id"] == rental_id:
            rental = r
            break
    if not rental:
        raise HTTPException(status_code=404, detail=f"Rental {rental_id} not found")
    if rental["status"] == "returned":
        raise HTTPException(status_code=400, detail="This rental has already been returned")

    rental["status"] = "returned"
    car = find_car(rental["car_id"])
    if car:
        car["is_available"] = True

    return {"message": "Car returned successfully", "rental": rental}