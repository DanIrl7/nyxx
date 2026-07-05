from files.image_process import process_image_for_terminal
img, palette = process_image_for_terminal(r"c:\Users\t430\3D Objects\coding\projects\Nyxx\files\my_photo.jpg", target_cols=80, target_lines=24)
print("size:", img.size)
print("mode:", img.mode)
print("palette entries:", len(palette))
img.save("processed_preview.png")