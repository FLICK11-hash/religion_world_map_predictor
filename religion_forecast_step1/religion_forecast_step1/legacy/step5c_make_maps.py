"""Generate summary maps from Step 5C without overwriting older figures."""
import step6_make_maps as maps
maps.FORECAST=maps.ROOT/'data'/'forecasts_step5c'
maps.OUT=maps.ROOT/'outputs'/'maps_step5c'
if __name__=='__main__':maps.main()
