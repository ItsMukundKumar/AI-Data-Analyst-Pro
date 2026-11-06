from io import BytesIO
from PIL import Image


def create_dashboard_image(chart_images: list[bytes]) -> bytes:
    if not chart_images:
        raise ValueError("No chart images available.")

    images = [
        Image.open(BytesIO(image_data)).convert("RGB") for image_data in chart_images
    ]

    try:
        thumbnail_width = 900
        resized_images = []

        for image in images:
            ratio = thumbnail_width / image.width
            new_height = int(image.height * ratio)

            resized_images.append(image.resize((thumbnail_width, new_height)))

        gap = 20
        columns = 2
        rows = (len(resized_images) + columns - 1) // columns

        row_heights = []

        for row in range(rows):
            row_images = resized_images[row * columns : (row + 1) * columns]
            row_heights.append(max(img.height for img in row_images))

        dashboard_height = sum(row_heights) + gap * (rows + 1)

        dashboard = Image.new(
            "RGB",
            (thumbnail_width * columns + gap * (columns + 1), dashboard_height),
            "white",
        )

        y_position = gap

        for row in range(rows):
            row_images = resized_images[row * columns : (row + 1) * columns]

            for column, image in enumerate(row_images):
                x_position = gap + column * (thumbnail_width + gap)

                dashboard.paste(image, (x_position, y_position))

            y_position += row_heights[row] + gap

        output = BytesIO()
        dashboard.save(output, format="JPEG", quality=85)

        return output.getvalue()

    finally:
        for image in images:
            image.close()
