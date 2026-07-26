"""
weather_context.py for FranchiseOps AI
Simulates local Indian city weather disruptions and logistics delays across franchise outlets.
"""
import random

CITY_WEATHER_REPORTS = {
    "Mumbai (MH)": {"status": "Heavy Monsoon Rain & Waterlogging", "temp_c": 28, "demand_impact_pct": -18.0, "supply_delay_days": 2, "attrition_stress": "High"},
    "Bengaluru (KA)": {"status": "Pleasant / Light Showers", "temp_c": 24, "demand_impact_pct": 12.0, "supply_delay_days": 0, "attrition_stress": "Normal"},
    "Delhi NCR (DL)": {"status": "Intense Summer Heatwave & Smog", "temp_c": 42, "demand_impact_pct": 15.0, "supply_delay_days": 1, "attrition_stress": "High"},
    "Hyderabad (TG)": {"status": "Clear & Warm", "temp_c": 33, "demand_impact_pct": 8.0, "supply_delay_days": 0, "attrition_stress": "Normal"},
    "Chennai (TN)": {"status": "Humid & Coastal Showers", "temp_c": 35, "demand_impact_pct": -5.0, "supply_delay_days": 1, "attrition_stress": "Medium"},
    "Pune (MH)": {"status": "Cloudy & Breezy", "temp_c": 26, "demand_impact_pct": 10.0, "supply_delay_days": 0, "attrition_stress": "Normal"},
    "Ahmedabad (GJ)": {"status": "Dry & High Heat", "temp_c": 40, "demand_impact_pct": -8.0, "supply_delay_days": 1, "attrition_stress": "Medium"},
    "Kolkata (WB)": {"status": "Thunderstorms & High Humidity", "temp_c": 32, "demand_impact_pct": -12.0, "supply_delay_days": 2, "attrition_stress": "High"}
}

def get_city_weather(city_name):
    for k, v in CITY_WEATHER_REPORTS.items():
        if k.lower() in city_name.lower() or city_name.lower() in k.lower():
            return {"city": k, **v}
    return {"city": city_name, "status": "Fair Weather Conditions", "temp_c": 30, "demand_impact_pct": 0.0, "supply_delay_days": 0, "attrition_stress": "Normal"}

def get_weather_report(port_name):
    return {"port": port_name, "status": "Normal Marine Conditions", "temp_c": 25, "wind_kt": 15, "delay_penalty_multiplier": 1.00}
