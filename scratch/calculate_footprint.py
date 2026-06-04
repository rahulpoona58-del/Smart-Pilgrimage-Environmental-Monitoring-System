import sqlite3
import os

def calculate():
    db_path = "database/buffer_v3.db"
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("==================================================")
    print("=== SPEMS Carbon Footprint & Emissions Calculator ===")
    print("==================================================")

    # 1. Fetch Vehicle Stats
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    total_vehicles = cursor.fetchone()[0]

    cursor.execute("SELECT emission_standard, COUNT(*) FROM vehicles GROUP BY emission_standard")
    emission_standards = cursor.fetchall()
    
    print(f"Total Registered Vehicles: {total_vehicles}")
    for standard, count in emission_standards:
        print(f"  - {standard}: {count} vehicles")

    # 2. Fetch Journey Logs
    cursor.execute("SELECT COUNT(*) FROM vehicle_logs")
    total_logs = cursor.fetchone()[0]
    print(f"Total Transit Logs (Entry/Exit): {total_logs}")

    # Estimate travel distance: Sonprayag-to-Gaurikund corridor is approx 6.0 kilometers
    distance_km = 6.0
    
    # Emission constants (grams of CO2 per km)
    # BS-IV Diesel: ~170g CO2/km, BS-IV Petrol: ~140g CO2/km
    # BS-VI Diesel: ~140g CO2/km, BS-VI Petrol: ~120g CO2/km
    # Multi-axle commercial coaches/heavy buses: ~750g CO2/km
    
    cursor.execute("""
        SELECT v.emission_standard, v.vehicle_type, COUNT(l.id) 
        FROM vehicle_logs l 
        JOIN vehicles v ON l.plate_number = v.plate_number 
        GROUP BY v.emission_standard, v.vehicle_type
    """)
    journey_stats = cursor.fetchall()

    total_co2_grams = 0
    total_pm_grams = 0 # Particulate Matter
    
    print("\nVehicle Emissions Analysis (By Journey Segments):")
    for standard, v_type, count in journey_stats:
        # Distance modeled as 1 direction transit per log
        segment_dist = count * distance_km
        
        # Determine emission factors
        if "bus" in v_type.lower() or "truck" in v_type.lower() or "commercial" in v_type.lower():
            co2_factor = 750.0
            pm_factor = 0.05
        else:
            if standard == "BS-VI":
                co2_factor = 130.0
                pm_factor = 0.005
            else:
                co2_factor = 160.0
                pm_factor = 0.025
        
        co2_emitted = segment_dist * co2_factor
        pm_emitted = segment_dist * pm_factor
        total_co2_grams += co2_emitted
        total_pm_grams += pm_emitted
        
        print(f"  - {v_type} ({standard}): {count} transits | Total CO2: {co2_emitted/1000:.2f} kg | PM: {pm_emitted:.2f} g")

    # 3. Route Emissions
    # Calculate Kedarnath Route total emissions
    total_co2_kg = total_co2_grams / 1000.0
    print(f"\n==================================================")
    print(f"Pilgrimage Route Carbon Footprint:")
    print(f"==================================================")
    print(f"Kedarnath Base Corridor Total CO2: {total_co2_kg:.2f} kg CO2e")
    print(f"Total Fine Particulates (PM) Released: {total_pm_grams:.2f} grams")

    # 4. Offset Recommendations
    # 1 mature tree absorbs approx 22 kg of CO2 per year
    trees_needed = int(total_co2_kg / 22.0) + 1
    
    # Financial carbon offset cost: ₹150 INR per tree plantation & maintenance
    offset_cost_inr = trees_needed * 150
    
    print(f"\n==================================================")
    print(f"Uttarakhand Government Offset Recommendations:")
    print(f"==================================================")
    print(f"1. Tree Plantation Target: {trees_needed} Deodar/Himalayan Oak saplings to neutralize footprint.")
    print(f"2. Environmental Mitigation Fund Allocation: INR {offset_cost_inr:,}")
    print(f"3. Idle-Reduction Policy: Implementing a strict 3-minute engine shutdown rule at Gaurikund parking will save approx {total_co2_kg * 0.18:.2f} kg CO2e annually.")
    print("==================================================")

    conn.close()

if __name__ == "__main__":
    calculate()
