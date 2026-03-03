import pandas as pd
import requests
import folium

# ============================================================
# Lab 6 - Hometown Map (Quito)
# What this script does:
# 1) reads my hometown_locations.csv
# 2) uses Mapbox to convert addresses into coordinates (lat/lon)
# 3) builds an interactive map with my custom Mapbox basemap
# 4) adds markers + popups (name, my description, image)
# ============================================================


MAPBOX_TOKEN = "pk.eyJ1Ijoia2NsYXZpam8xIiwiYSI6ImNtbHRwcHpnZjAydHQzaXEyemYybWpmM2cifQ.8LL88HyDwD8Icfbgpsk86g"
MAPBOX_STYLE = "mapbox://styles/kclavijo1/cmm82goq900mk01s5cagud9g5"

QUITO_PROXIMITY = "-78.4678,-0.1807"     
QUITO_BBOX = "-78.65,-0.40,-78.30,0.10" 



def style_to_tiles(style_url: str, token: str) -> str:
    """
    Folium needs a tile URL, but Mapbox gives a style URL.
    This converts: mapbox://styles/user/styleid
    into a working tiles URL.
    """
    clean = style_url.replace("mapbox://styles/", "")
    user, style_id = clean.split("/")
    return f"https://api.mapbox.com/styles/v1/{user}/{style_id}/tiles/256/{{z}}/{{x}}/{{y}}@2x?access_token={token}"


def geocode_one(address: str, token: str):
    # Mapbox Geocoding API v5 (more reliable for class tokens)
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json".format(
        requests.utils.quote(address)
    )

    params = {
        "access_token": token,
        "limit": 1,
        "country": "ec",
        "proximity": QUITO_PROXIMITY,
        # comment this out first if it still struggles:
        "bbox": QUITO_BBOX
    }

    resp = requests.get(url, params=params, timeout=20)

    # if something is wrong with the token or API, show the message
    if resp.status_code != 200:
        print("Mapbox error:", resp.status_code, resp.text)
        return (None, None)

    data = resp.json()

    features = data.get("features", [])
    if len(features) == 0:
        return None, None

    coords = features[0]["geometry"]["coordinates"]  # [lon, lat]
    lon = coords[0]
    lat = coords[1]
    return lat, lon


def pick_color(place_type: str) -> str:
    """
    Simple color rules. If you only have restaurants, they’ll all be red.
    You can add more types later.
    """
    t = str(place_type).strip().lower()

    if "restaurant" in t:
        return "red"
    if "cafe" in t:
        return "orange"
    if "park" in t:
        return "green"
    if "cultural" in t or "museum" in t:
        return "purple"

    return "gray"


def make_popup_html(name: str, desc: str, img_url: str, place_type: str) -> str:
    """
    Builds the popup box you see when you click a marker.
    """
    return f"""
    <div style="width:260px;">
      <div style="font-weight:700; font-size:14px; margin-bottom:6px;">{name}</div>
      <div style="font-size:12px; line-height:1.35; margin-bottom:8px;">{desc}</div>
      <img src="{img_url}" style="width:100%; border-radius:10px; margin-bottom:6px;" />
      <div style="font-size:11px; color:#555;"><b>Type:</b> {place_type}</div>
    </div>
    """


def main():
    # 1) read the csv
    csv_path = "lab6/hometown_locations.csv"
    df = pd.read_csv(csv_path)


    needed = ["Name", "Address", "Type", "Description", "Image_URL"]
    for col in needed:
        if col not in df.columns:
            raise ValueError(f"Missing column in CSV: {col}")

    # 2) geocode every row
    lat_list = []
    lon_list = []

    print("Geocoding addresses (this can take a minute)...")

    for i, row in df.iterrows():
        address = str(row["Address"])
        lat, lon = geocode_one(address, MAPBOX_TOKEN)

        if lat is None:
            print(f"⚠️ Could not find: {address}")
        else:
            print(f"✅ {i+1}/{len(df)} found")

        lat_list.append(lat)
        lon_list.append(lon)

    df["Lat"] = lat_list
    df["Lon"] = lon_list
    df = df.dropna(subset=["Lat", "Lon"]).reset_index(drop=True)

    if df.empty:
        raise ValueError("No addresses were geocoded. Check your token + addresses.")

    # 3) build the map and add your custom basemap
    tiles_url = style_to_tiles(MAPBOX_STYLE, MAPBOX_TOKEN)

    center_lat = df["Lat"].mean()
    center_lon = df["Lon"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles=None)

    folium.TileLayer(
        tiles=tiles_url,
        attr="Mapbox",
        name="My custom basemap"
    ).add_to(m)

    # 4) add markers
    for _, row in df.iterrows():
        name = str(row["Name"])
        place_type = str(row["Type"])
        desc = str(row["Description"])
        img = str(row["Image_URL"])

        popup_html = make_popup_html(name, desc, img, place_type)
        popup = folium.Popup(popup_html, max_width=300)

        folium.Marker(
            location=[row["Lat"], row["Lon"]],
            tooltip=name,
            popup=popup,
            icon=folium.Icon(color=pick_color(place_type), icon="info-sign")
        ).add_to(m)

    folium.LayerControl().add_to(m)

    # 5) save the HTML
    out_file = "hometown_map.html"
    m.save(out_file)
    print(f"\nDONE ✅ Open this file in your browser: {out_file}")


if __name__ == "__main__":
    main()