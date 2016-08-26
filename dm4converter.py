import Tkinter as tk
from Tkinter import *
import tkFileDialog as filedialog

import os
import dm4reader
from PIL import Image, ImageTk

import numpy as np

class Dm4Converter(tk.Frame):
    def __init__(self, root, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.parent = root
        self.src_string = StringVar()
        self.src_string.set('C:\\Source')
        self.output_string = StringVar()
        self.output_string.set('C:\\Temp')
        self.status_string = StringVar()
        self.brightness = IntVar()
        self.brightness.set(10)
        self.src_string.trace('w', lambda *args: self.update_status(0))
        self.preview_image = None
        
        self.create()
        
        self.update_status(0)
        self.preview_change()
        
    def create(self):
        # Source folder select row
        in_frame = Frame(self)
        in_frame.pack()
        in_label = Label(in_frame, text='Source Folder', width=12)
        in_label.pack(side = LEFT, pady=5)        
        in_text = Entry(in_frame, textvariable=self.src_string)
        in_text.pack(side=LEFT, padx=5, pady=5)
        
        in_button = Button(in_frame,
                           text='Browse',
                           command = lambda: self.get_folder(self.src_string, 'Select a source folder'))
        in_button.pack(side = LEFT, padx=5, pady=5)
        
        #Output folder select row
        out_frame = Frame(self)
        out_frame.pack()
        out_label = Label(out_frame, text='Output Folder', width=12)
        out_label.pack(side = LEFT, pady=5)
        out_text = Entry(out_frame, textvariable=self.output_string)
        out_text.pack(side=LEFT, padx=5, pady=5)

        out_button = Button(out_frame,
                            text='Browse',
                            command = lambda: self.get_folder(self.output_string, 'Select an output folder'))
        out_button.pack(side = LEFT, padx=5, pady=5)

        bright_frame = Frame(self)
        bright_frame.pack(fill=X)
        bright_label = Label(bright_frame, text='Brightness')
        bright_label.pack(side=LEFT, padx=5, pady=5)
        bright_text = Entry(bright_frame, textvariable=self.brightness, width=4)
        bright_text.pack(side=LEFT, padx=5, pady=5)
        
        # Confirm/Cancel row
        confirm_frame = Frame(self)
        confirm_frame.pack(fill=X)
        status_label = Label(confirm_frame, textvariable=self.status_string, width=20)
        status_label.pack(side=LEFT, padx=5, pady=5)
        ok_button = Button(confirm_frame,
                           text='OK',
                           command=self.convert)
        ok_button.pack(side=RIGHT, padx=5, pady=5)

        close_button = Button(confirm_frame, text='Close', command=root.destroy)
        close_button.pack(side=RIGHT, padx=5, pady=5)
        
        # Create preview image row
        preview_frame = Frame(self)
        preview_frame.pack()

        view_button = Button(preview_frame, text='Preview', command=self.preview_change)
        view_button.pack(anchor=W, pady=5)

        pic_frame = Frame(preview_frame, height=256, width=256, relief=SUNKEN, borderwidth=1)
        pic_frame.pack_propagate(0)
        pic_frame.pack()

        img_label = Label(pic_frame)
        img_label.pack(fill=BOTH, expand=1)
        self.preview_image = img_label
    
    def update_status(self, processed):
        dm4_file_count = len(self.get_dm4_filenames())
        
        self.status_string.set('' + str(processed) + ' of ' + str(dm4_file_count) + ' files processed')
    
    def get_dm4_filenames(self):
        src_folder = self.src_string.get()
        src_filenames = [f for f in os.listdir(src_folder) 
                if os.path.isfile(os.path.join(src_folder, f))]
        dm4_filenames = [f for f in src_filenames
                if os.path.splitext(f)[1] == '.dm4']
                
        return dm4_filenames
    
    # Update the preview image
    def preview_change(self):
        src_folder = self.src_string.get()
        if self.brightness.get():
            dm4_filenames = self.get_dm4_filenames()
            if len(dm4_filenames):
                dm4_fullpath = os.path.join(src_folder, dm4_filenames[0])
                
                dm4_file = dm4reader.DM4File.open(dm4_fullpath)
                dm4_tags = dm4_file.read_directory()
                data_tag = dm4_tags.named_subdirs['ImageList'].unnamed_subdirs[1].named_subdirs['ImageData'].named_tags['Data']
                np_array = np.array(dm4_file.read_tag_data(data_tag), dtype=np.uint16)
                np_array = np.reshape(np_array, Dm4Converter.read_image_shape(dm4_file, dm4_tags))
                
                # ImageTk doesn't seem to handle 16bit greyscale so by brightness value and then
                # rescale to 8 bit values.
                grey_array = np_array * self.brightness.get() / 256
                
                image = Image.fromarray(grey_array, 'I;16')
                image = image.resize((256, 256))
                
                tk_preview = ImageTk.PhotoImage(image)
                
                self.preview_image.configure(image=tk_preview)
                self.preview_image.image = tk_preview
            else:
                self.preview_image.configure(image=None)
                self.preview_image.image = None
        
        
    
    def get_folder(self, textvar, display):
        folder = filedialog.askdirectory(initialdir=textvar.get(), title=display)
        if folder:
            textvar.set(folder)
    
    @staticmethod
    def image_dimension_tag(dm4_tags):
        return dm4_tags.named_subdirs['ImageList'].unnamed_subdirs[1].named_subdirs['ImageData'].named_subdirs['Dimensions']
        
    @staticmethod    
    def read_image_shape(dm4_file, dm4_tags):
        dimension_tag = Dm4Converter.image_dimension_tag(dm4_tags)
        XDim = dm4_file.read_tag_data(dimension_tag.unnamed_tags[0])
        YDim = dm4_file.read_tag_data(dimension_tag.unnamed_tags[1])
        
        return (YDim, XDim)
        
    def convert(self):
        dm4_filenames = self.get_dm4_filenames()
        
        src_folder = self.src_string.get()
        output_dir = self.output_string.get()
        
        files_processed = 0
        
        for filename in dm4_filenames:
            dm4_fullpath = os.path.join(src_folder, filename)
            
            file_basename = os.path.basename(filename)
            output_filename = os.path.basename(file_basename + '.tif')
        
            output_path = os.path.join(output_dir, output_filename)
            
            dm4_file = dm4reader.DM4File.open(dm4_fullpath)
            dm4_tags = dm4_file.read_directory()
            data_tag = dm4_tags.named_subdirs['ImageList'].unnamed_subdirs[1].named_subdirs['ImageData'].named_tags['Data']
            np_array = np.array(dm4_file.read_tag_data(data_tag), dtype=np.uint16)
            np_array = np.reshape(np_array, Dm4Converter.read_image_shape(dm4_file, dm4_tags))
        
            grey_array = np_array * self.brightness.get()
            
            image = Image.fromarray(grey_array, 'I;16')
            image.save(output_path)
            
            files_processed += 1
            self.update_status(files_processed)
            
            dm4_file.close()

if __name__ == '__main__':
    root = tk.Tk()
    root.title('DM4 Converter')
    root.resizable(0,0)
    dm4 = Dm4Converter(root)
    dm4.pack()

    root.mainloop()

