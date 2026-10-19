"""Render Step 5B scenario maps without changing the existing Step 6 outputs."""
import step6_make_maps as maps
maps.FORECAST=maps.ROOT/'data'/'forecasts_step5b'
maps.OUT=maps.ROOT/'outputs'/'maps_step5b'
if __name__=='__main__':
    maps.main()
