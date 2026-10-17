def preprocess_landmarks(hand_landmarks):
    
    # Extracting the [x, y] coordinates for each landmark
    coords = [[lm.x, lm.y] for lm in hand_landmarks]

    # Converting to relative coordinates based on the ID:0 landmark (wrist)
    base_x, base_y = coords[0]
    relative_coords = []
    for x, y in coords:
        relative_coords.append([x - base_x, y - base_y])

    # Flattening to a one-dimensional array
    flattened = []
    for x, y in relative_coords:
        flattened.append(x)
        flattened.append(y)
    
    # Normalizing to the maximum absolute value
    max_value = max([abs(val) for val in flattened])

    if max_value:
        normalized = [val / max_value for val in flattened]
    else:
        normalized = flattened

    return normalized