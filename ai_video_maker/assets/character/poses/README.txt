Character pose library for AI Visual Storyteller V3.1.

The 15 supported transparent PNG assets are:
idle.png, curious.png, surprised.png, thinking.png, explaining.png,
point_left.png, point_right.png, compare.png, warning.png, confident.png,
happy.png, questioning.png, sitting.png, stretching.png, working.png.

main.png in the parent character folder remains the identity reference.
The compositor selects the requested character_pose PNG. If an asset is missing,
it logs a warning and falls back to main.png. The home page Pose Library can
generate missing assets or explicitly regenerate one pose when an API key is set.

The existing pose PNGs were generated from the master character reference with
the built-in image generation tool and copied into this project. They use an
alpha background. Idle is a copy of the master character.
