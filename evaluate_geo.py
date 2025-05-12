import pandas as pd
import argparse
import numpy as np

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pred_csv', type=str, required=True, help='Path to the prediction CSV file')
    parser.add_argument('--dataset', type=str, required=True, help='Which dataset to evaluate on (xcdc or inat)')
    args = parser.parse_args()
    return args



def check_min_max(ar, min_val, max_val):
    return ar.min() >= min_val and ar.max() <= max_val
    
def geodesic_distance(loc1, loc2):
    lat1, lon1 = loc1[..., 0], loc1[..., 1] 
    lat2, lon2 = loc2[..., 0], loc2[..., 1] 
    assert check_min_max(lat1, -90, 90) and check_min_max(lon1, -180, 180), "Latitude and longitude must be in the range [-90, 90] and [-180, 180] respectively."
    assert check_min_max(lat2, -90, 90) and check_min_max(lon2, -180, 180), "Latitude and longitude must be in the range [-90, 90] and [-180, 180] respectively."
    r = 6371 # Earth radius in kilometers
    # Haversine formula
    phi1, phi2 = np.deg2rad(lat1), np.deg2rad(lat2)
    delta_phi, delta_lambda = np.deg2rad(lat2-lat1), np.deg2rad(lon2-lon1)
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    return 2 * r * np.arcsin(np.sqrt(a))

distance_thresholds = {
    "street": 1,
    "city": 25,
    "region": 200,
    "country": 750,
    "continent": 2500,
}


def evaluate_geo(pred_csv, gold_csv):
    # Load the prediction and ground truth CSV files
    pred_df = pd.read_csv(pred_csv)
    gold_df = pd.read_csv(gold_csv)

    # check if audio_ids in both match
    assert set(pred_df['audio_id']) == set(gold_df['audio_id']), "Audio IDs in prediction and ground truth do not match."

    # get lat lons from both in matching order
    gold_audio_id2latlon = {audio_id: (lat, lon) for audio_id, lat, lon in zip(gold_df['audio_id'], gold_df['latitude'], gold_df['longitude'])}
    pred_audio_id2latlon = {audio_id: (lat, lon) for audio_id, lat, lon in zip(pred_df['audio_id'], pred_df['latitude'], pred_df['longitude'])}
    
    gold_lat_lons = np.array([gold_audio_id2latlon[audio_id] for audio_id in gold_audio_id2latlon])
    pred_lat_lons = np.array([pred_audio_id2latlon[audio_id] for audio_id in gold_audio_id2latlon])


    distances = geodesic_distance(pred_lat_lons, gold_lat_lons)

    metric_dict = {
        "mean_error": np.mean(distances),
        "median_error": np.median(distances),
    }
    for scale, threshold in distance_thresholds.items():
        metric_dict[scale] = np.mean(distances <= threshold)
    return metric_dict


if __name__ == "__main__":
    args = get_args()
    if args.dataset == "xcdc":
        gold_csv = "./ground_truths/xcdc_gold.csv"
    elif args.dataset == "inat":
        gold_csv = "./ground_truths/inat_test_gold.csv"
    else:
        raise ValueError("Dataset must be either xcdc or inat")
    metric_dict = evaluate_geo(args.pred_csv, gold_csv)
    print(metric_dict)