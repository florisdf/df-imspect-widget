from ipywidgets import HBox, VBox, BoundedIntText, Dropdown
from typing import List, Callable, Union
import pandas as pd
from .example import ImBoxWidget, CropBoxWidget, DetailsWidget


class ImBox(VBox):
    """Widget for inspecting images that contain bounding boxes."""
    def __init__(self, df: pd.DataFrame, box_col: str = 'box',
                 img_col: str = 'image',
                 text_cols: Union[str, List[str]] = None,
                 text_fmts: Union[Callable, List[Callable]] = None,
                 style_col: str = None):
        """
        :param pd.DataFrame df: `DataFrame` with images and boxes
        :param str box_col: column in the dataframe that contains boxes
        :param str img_col: column in the dataframe that contains image paths
        :param Union[str, List[str]] text_cols: (optional) the column(s) in the
        dataframe to use for creating the text that is shown on top of a box.
        When multiple columns are give, the text will be created by a
        comma-separated list of the contents of the given columns.
        :param Unions[Callable, List[Callable]] text_fmts: (optional) a
        callable, or list of callables, that takes the corresponding value from
        the `text_cols` column(s) as an input and returns the string to print
        for that value.
        :param str style_col: the column containing a dict of style attributes.
        Available attributes are:
            - `stroke_width`: the stroke width of a box (default 2)
            - `stroke_style`: the stroke color of a box (default 'red')
            - `fill_style`: the fill color of a box (default  '#00000000')
            - `hover_fill`: the fill color of a box when it is hovered on
              (default '#00000088')
            - `hover_stroke`: the stroke color of a box when it is hovered on
              (default 'blue')
            - `active_fill`: the fill color of a box when it is clicked on
              (default '#ffffff22')
            - `active_stroke`: the stroke color of a box when it is clicked on
              (default 'green')
            - `font`: the font to use for box text (default '10px sans-serif')
        """
        if text_cols is None:
            text_cols = []
        if isinstance(text_cols, str):
            text_cols = [text_cols]
        if text_fmts is None:
            text_fmts = [None]*len(text_cols)
        if isinstance(text_fmts, Callable):
            text_fmts = [text_fmts]
        self.text_cols = text_cols
        self.text_fmts = text_fmts

        df2 = df.copy()

        def row2text(row):
            txts = row[text_cols]
            return ', '.join([fmt(txt) if fmt is
                              not None else
                              str(txt)
                              for txt, fmt in zip(txts, self.text_fmts)])

        df2['box_text'] = df2.apply(lambda row: row2text(row), axis=1)
        df2['box_dict'] = df2.apply(lambda row: dict(index=row.name,
                                                     box=row[box_col],
                                                     text=row['box_text'],
                                                     style=row[style_col]
                                                     if style_col is not None
                                                     else {})
                                    if (box_col in row.index
                                        and row[box_col] is not None)
                                    else None,
                                    axis=1)

        self.df_img = df2.groupby(img_col).agg(list).reset_index()

        self.imbox_wgt = ImBoxWidget()
        self.crop_wgt = CropBoxWidget()
        self.detail_wgt = DetailsWidget()

        self.idx_wgt = BoundedIntText(value=None,
                                      min=0,
                                      max=len(self.df_img) - 1,
                                      step=1,
                                      description='Index',
                                      disabled=False)

        self.drop_wgt = Dropdown(options=self.df_img[img_col],
                                 description='Image',
                                 value=None,
                                 disabled=False)
        self.df = df
        self.img_col = img_col
        self.box_col = box_col

        self.imbox_wgt.observe(self.box_changed, names='active_box')
        self.imbox_wgt.observe(self.img_changed, names='img')
        self.drop_wgt.observe(self.drop_changed, names='value')
        self.idx_wgt.observe(self.idx_changed, names='value')
        super().__init__([self.drop_wgt,
                          self.idx_wgt,
                          HBox([self.imbox_wgt,
                                VBox([self.crop_wgt,
                                      self.detail_wgt])])])

    def box_changed(self, change):
        if change['new'] is None:
            self.detail_wgt.data = {}
            self.crop_wgt.box = None
        else:
            new_idx = change['new']['index']
            self.detail_wgt.data = dict(self.df.loc[new_idx])
            self.crop_wgt.box = change['new']['box']

    def img_changed(self, change):
        new_img = change['new']
        self.detail_wgt.data = {}
        self.crop_wgt.img = new_img

    def drop_changed(self, change):
        idx = self.df_img[self.df_img[self.img_col] == change['new']].index[0]
        self.imbox_wgt.img = self.df_img.loc[idx, self.img_col]
        self.imbox_wgt.boxes = self.df_img.loc[idx, 'box_dict']
        self.idx_wgt.value = idx

    def idx_changed(self, change):
        idx = change['new']
        self.imbox_wgt.img = self.df_img.loc[idx, self.img_col]
        self.imbox_wgt.boxes = self.df_img.loc[idx, 'box_dict']
        self.drop_wgt.value = self.imbox_wgt.img
