import pygame
from pathlib import Path
import os
from typing import Union, List, Optional
import argparse

background_color: tuple[int, int, int] = (255, 255, 255)
text_color: tuple[int, int, int] = (0, 0, 0)


class Slide:
    def __init__(self) -> None:
        self._lines: List[str] = []
        self._image: Optional[pygame.Surface] = None

    def set_image(self, image_path: Path) -> None:
        self._image = pygame.image.load(image_path)

    def set_lines(self, lines: List[str]) -> None:
        self._lines = lines

    def get_content(self) -> Union[pygame.Surface, List[str]]:
        if self._image:
            return self._image
        else:
            return self._lines


class Presentation:
    def __init__(self) -> None:
        self._slides: List[Slide] = []
        self._current_slide: int = 0

    def add_slide(self, slide: Slide) -> None:
        self._slides.append(slide)

    def get_current_slide(self) -> Slide:
        return self._slides[self._current_slide]

    def next(self) -> None:
        self._current_slide = min(self._current_slide + 1, len(self._slides) - 1)

    def prev(self) -> None:
        self._current_slide = max(self._current_slide - 1, 0)


def parse(filename: Path) -> Presentation:
    with open(filename, "r") as f:
        paragraphs = f.read().split("\n\n")

    pres = Presentation()

    for par in paragraphs:
        slide = Slide()
        if par.startswith("@"):
            # This is an image
            par = par.removeprefix("@")
            image = par.split()[0]
            slide.set_image(Path(image))
        else:
            # This is plain text
            lines = par.split("\n")

            lines = list(filter(lambda x: not x.startswith("#"), lines))

            lines = list(map(lambda line: line.removeprefix("\\"), lines))
            slide.set_lines(lines)

        pres.add_slide(slide)

    return pres


def draw_centered_image_with_padding(
    screen: pygame.Surface,
    image: pygame.Surface,
    screen_width: int,
    screen_height: int,
    horizontal_padding: float,
    vertical_padding: float,
) -> None:
    screen.fill(background_color)

    padding_x = screen_width * horizontal_padding
    padding_y = screen_height * vertical_padding

    available_width = screen_width - 2 * padding_x
    available_height = screen_height - 2 * padding_y

    original_width, original_height = image.get_size()

    aspect_ratio = original_width / original_height

    if available_width / available_height > aspect_ratio:
        new_height = available_height
        new_width = int(new_height * aspect_ratio)
    else:
        new_width = available_width
        new_height = int(new_width / aspect_ratio)

    image = pygame.transform.scale(image, (new_width, new_height))

    image_width, image_height = image.get_size()

    x = (screen_width - image_width) // 2
    y = (screen_height - image_height) // 2

    screen.blit(image, (x, y))

    pygame.display.flip()


def draw_centered_text(
    screen: pygame.Surface,
    strings: List[str],
    screen_width: int,
    screen_height: int,
    horizontal_padding: float,
    vertical_padding: float,
) -> None:
    screen.fill(background_color)

    horizontal_padding = screen_width * horizontal_padding
    vertical_padding = screen_height * vertical_padding

    available_width = screen_width - 2 * horizontal_padding
    available_height = screen_height - 2 * vertical_padding

    max_font_size = 1
    font_name = pygame.font.get_default_font()

    while True:
        font = pygame.font.Font(font_name, max_font_size)
        total_height = (
            sum(font.size(string)[1] for string in strings) + (len(strings) - 1) * 10
        )
        max_width = max(font.size(string)[0] for string in strings)

        if total_height > available_height or max_width > available_width:
            break

        max_font_size += 1

    max_font_size -= 1
    font = pygame.font.Font(font_name, max_font_size)

    total_height = (
        sum(font.size(string)[1] for string in strings) + (len(strings) - 1) * 10
    )
    y = vertical_padding + (available_height - total_height) // 2

    for string in strings:
        text_surface = font.render(string, True, text_color)
        screen.blit(text_surface, (horizontal_padding, y))
        y += text_surface.get_height() + 10

    pygame.display.flip()


def main(presentation_path: Path) -> None:
    pres = parse(presentation_path)
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()

    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h

    screen = pygame.display.set_mode(
        (screen_width, screen_height), pygame.WINDOWMAXIMIZED
    )
    pygame.display.set_caption("pysent")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    pres.next()
                elif event.key == pygame.K_LEFT:
                    pres.prev()
                elif event.key == pygame.K_q:
                    running = False

        content = pres.get_current_slide().get_content()
        if isinstance(content, list):
            draw_centered_text(screen, content, screen_width, screen_height, 0.1, 0.1)
        else:
            draw_centered_image_with_padding(
                screen, content, screen_width, screen_height, 0.1, 0.1
            )

    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a slide presentation from a text file."
    )
    parser.add_argument(
        "file", type=Path, help="Path to the .txt file containing the presentation data"
    )
    args = parser.parse_args()

    if args.file.exists() and args.file.suffix == ".txt":
        main(args.file)
    else:
        print("Invalid file. Please provide a valid .txt file.")
