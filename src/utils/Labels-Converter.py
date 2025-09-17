import os

# Paths
labels_dir = "./Polygon_Labels"   # folder with your current polygon labels
output_dir = "./Box_Labels"      # folder for converted box labels
os.makedirs(output_dir, exist_ok=True)

for file in os.listdir(labels_dir):
    if not file.endswith(".txt"):
        continue

    input_path = os.path.join(labels_dir, file)
    output_path = os.path.join(output_dir, file)

    with open(input_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) <= 5:
            # Already a box label
            new_lines.append(line.strip())
            continue

        cls = parts[0]
        coords = list(map(float, parts[1:]))

        # Split into x,y pairs
        xs = coords[0::2]
        ys = coords[1::2]

        # Bounding box
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)

        # Convert to YOLO box format
        x_center = (xmin + xmax) / 2
        y_center = (ymin + ymax) / 2
        width = xmax - xmin
        height = ymax - ymin

        new_line = f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
        new_lines.append(new_line)

    # Save new file
    with open(output_path, "w") as f:
        f.write("\n".join(new_lines))

print("✅ Conversion complete! Box labels saved in:", output_dir)
