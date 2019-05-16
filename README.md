df-imspect-widget
===============================

Pandas DataFrame inspector for images with boxes

Installation
------------

To install use pip:

    $ pip install dfimspect
    $ jupyter nbextension enable --py --sys-prefix dfimspect


For a development installation (requires npm),

    $ git clone https://github.com/florisdf/df-imspect-widget.git
    $ cd df-imspect-widget
    $ pip install -e .
    $ jupyter nbextension install --py --symlink --sys-prefix dfimspect
    $ jupyter nbextension enable --py --sys-prefix dfimspect

Usage
-----
```python
import dfimspect
dfimspect.ImBox(df=dataframe,
                img_col='column_with_image_paths',
                box_col='column_with_boxes')
```

The `DataFrame` instance contains data like this:

| **column_with_image_paths** | **column_with_boxes** | **some_info**| **extra_info** |
|-----------------------------|-----------------------|--------------|----------------|
| '/home/john/Pictures/IMG_1.jpg' | `Box(0, 1, 10, 5)` | 'Dirk'       | 0.9          |
| '/home/john/Pictures/IMG_1.jpg' | `Box(20, 100, 120, 210)` | 'Erik' | 0.85 |
| '/home/john/Pictures/IMG_2.jpg' | `Box(20, 100, 120, 210)` | 'Sandra' | 0.89 |

Where `Box` is an instance implementing the [`flutil.shape`](https://gitlab.com/EAVISE/flutil/tree/master/shape) `Box` class.
