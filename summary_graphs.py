import csv
import json
import os.path
import matplotlib.pyplot as plt


def load_frames_data(file_path):
    """Load 'frames pos.json' data."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return {}

    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON from {file_path}. Ensure the file structure is correct.")
        return {}



def read_results(file_path):
    """Read data from 'result.txt'."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []

    try:
        with open(file_path, 'r') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []



def process_data(frames_data, results):
    """Process results and frames data to extract required metrics."""
    frames = frames_data.get("frames", {})
    frame_names = set()
    table_data = []
    plot_data = {comp: [] for comp in frames.keys()}
    img_names = []

    for line in results:
        try:
            img_name, json_data = line.strip().split("--")
            row_data = {"img_name": img_name}

            # Parse JSON and compute metrics
            for frame_name, vel_data in json.loads(json_data).items():
                frame_names.add(frame_name)
                # Get 'OK' cases for the frame
                ok_case = frames.get(frame_name, {}).get('res_show', {}).get('OK', [])
                ok_case_total_vel = sum(percent for case_name, percent in vel_data.items() if case_name in ok_case)

                row_data[frame_name] = ok_case_total_vel
                plot_data[frame_name].append(ok_case_total_vel)

            img_names.append(img_name)
            table_data.append(row_data)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error processing line: {line}. Error: {e}")

    return sorted(frame_names), table_data, plot_data, img_names


def export_to_csv(file_path, frame_names, table_data):
    """Export data to CSV."""
    try:
        with open(file_path, 'w', newline='') as csvfile:
            fieldnames = ["img_name"] + frame_names
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in table_data:
                # Ensure missing columns have a blank value
                row = {frame: row.get(frame, "") for frame in fieldnames}
                writer.writerow(row)

        print(f"CSV table successfully saved to {file_path}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}")



def plot_data(plot_data, img_names,output_plot_file):
    """Generate and display plot."""
    plt.figure(figsize=(12, 8))

    for comp, values in plot_data.items():
        plt.scatter(img_names, values, label=comp)  # Scatter plot for readability
        # plt.plot(img_names,values)

    # Customize graph
    plt.title("Status Over Time")
    plt.xlabel("Data")
    plt.ylabel("% OK")
    plt.ylim(0, 100)
    plt.legend(loc="upper right", fontsize=8)
    plt.xticks(rotation=90)
    plt.tight_layout()

    plt.savefig(output_plot_file)
    plt.show()


def summary(main_path):
    # File paths (configurable)
    frames_file = os.path.join(main_path, "frames pos.json")
    results_file = os.path.join(main_path, "img_result", "result.txt")
    output_csv_file = os.path.join(main_path, "img_result.csv")
    output_plot_file = os.path.join(main_path, "img_result_plot.png")

    # Load data
    frames_data = load_frames_data(frames_file)
    results = read_results(results_file)

    # Validate input data
    if not frames_data or not results:
        print("Error: Missing or invalid input files.")
        return

    # Process data and generate outputs
    frame_names, table_data, plot_data_values, img_names = process_data(frames_data, results)
    export_to_csv(output_csv_file, frame_names, table_data)
    plot_data(plot_data_values, img_names,output_plot_file)


if __name__ == "__main__":
    main_path = r'C:\PythonProjects\auto_inspection_data__POWER-SUPPLY-FIXING-UNIT'
    summary(main_path)
