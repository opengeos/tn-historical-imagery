import os
import leafmap
import solara
import ipywidgets as widgets
import pandas as pd
import geopandas as gpd
import tempfile
from shapely.geometry import Point


def add_widgets(m):
    style = {"description_width": "initial"}
    padding = "0px 0px 0px 5px"

    checkbox = widgets.Checkbox(
        value=True,
        description="Footprints",
        style=style,
        layout=widgets.Layout(width="90px", padding="0px"),
    )

    split = widgets.Checkbox(
        value=False,
        description="Split map",
        style=style,
        layout=widgets.Layout(width="92px", padding=padding),
    )

    reset = widgets.Checkbox(
        value=False,
        description="Reset",
        style=style,
        layout=widgets.Layout(width="75px", padding="0px"),
    )

    output = widgets.Output()

    def reset_map(change):
        if change.new:
            pass

    reset.observe(reset_map, names="value")

    def handle_click(**kwargs):
        if kwargs.get("type") == "click":
            latlon = kwargs.get("coordinates")
            geometry = Point(latlon[::-1])
            selected = m.gdf[m.gdf.intersects(geometry)]
            setattr(m, "zoom_to_layer", False)
            if len(selected) > 0:
                filename = selected.iloc[0]["Filename"]
                county = selected.iloc[0]["County"]
                year = filename.split("_")[-1][:4]
                with output:
                    output.clear_output()
                    output.append_stdout(f"County: {county} | Year: {year}")
                url = f"https://data.source.coop/giswqs/tn-imagery/imagery/{filename}"
                layer = m.find_layer("Selected Image")
                if layer is not None:
                    m.remove(layer)
                m.default_style = {"cursor": "wait"}
                m.add_cog_layer(url, name="Selected Image", zoom_to_layer=False)
                m.default_style = {"cursor": "default"}
            else:
                with output:
                    output.clear_output()
                    output.append_stdout("No image found.")

    m.on_interaction(handle_click)

    box = widgets.VBox([widgets.HBox([checkbox, split, reset]), output])
    m.add_widget(box, position="topright", add_header=False)


zoom = solara.reactive(8)
center = solara.reactive((35.64836915737426, -86.21246337890626))


class Map(leafmap.Map):
    def __init__(self, **kwargs):
        kwargs["toolbar_control"] = False
        kwargs["draw_control"] = False
        super().__init__(**kwargs)
        basemap = {
            "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            "attribution": "Google",
            "name": "Google Satellite",
        }
        self.add_tile_layer(**basemap, shown=False)

        wms_url = "https://tnmap.tn.gov/arcgis/services/BASEMAPS/IMAGERY_WEB_MERCATOR/MapServer/WMSServer"
        self.add_wms_layer(wms_url, layers="0", name="TDOT Imagery", shown=True)

        self.add_layer_manager(opened=False)
        # add_widgets(self)
        geojson = "https://github.com/opengeos/datasets/releases/download/vector/TN_Counties.geojson"
        style = {"color": "#3388ff", "opacity": 1, "weight": 2, "fillOpacity": 0}
        self.add_geojson(
            geojson,
            layer_name="TN Counties",
            style=style,
            zoom_to_layer=False,
            info_mode=None,
        )
        gdf = gpd.read_file(geojson)
        setattr(self, "gdf", gdf)
        add_widgets(self)


@solara.component
def Page():
    with solara.Column(style={"min-width": "500px"}):
        # solara components support reactive variables
        # solara.SliderInt(label="Zoom level", value=zoom, min=1, max=20)
        # using 3rd party widget library require wiring up the events manually
        # using zoom.value and zoom.set
        Map.element(  # type: ignore
            zoom=zoom.value,
            on_zoom=zoom.set,
            center=center.value,
            on_center=center.set,
            scroll_wheel_zoom=True,
            toolbar_ctrl=False,
            data_ctrl=False,
            height="780px",
        )
        # solara.Text(f"Center: {center.value}")
        # solara.Text(f"Zoom: {zoom.value}")