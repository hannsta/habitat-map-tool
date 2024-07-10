import React, { useEffect, useState } from 'react';
import logo from './logo.svg';
import './App.css';
import { HiLockClosed, HiLockOpen } from 'react-icons/hi';
import { LatLngBoundsExpression, LatLngExpression, LatLngTuple } from 'leaflet';
import { GeoJSON, MapContainer, TileLayer, Marker, Popup, Rectangle, useMapEvents } from 'react-leaflet';
import markerIconPng from "leaflet/dist/images/marker-icon.png"
import {Icon} from 'leaflet'

//import bad_data.geojson from './bad_data.geojson'
//@ts-ignore
import bad_data from './bad_data.json'
import LevelList from './LevelList';
import LevelConfig from './LevelConfig';

const BASE_URL = 'http://127.0.0.1:5000/'

export interface HabitatMapLevel {
  name: string;
  id: string;
  centerPoint: number[];
  boundHeight: number;
  hasBeenProcessed: boolean;
}
const baseMapsURLs = {
    'OpenStreetMap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'OpenTopoMap': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    'Esri World Imagery': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    'Satellite': 'https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg'
}

function App() {
  const [moveBox, setMoveBox] = useState<boolean>(true);
  const [baseMap, setBaseMap] = useState<string>('OpenStreetMap' as keyof typeof baseMapsURLs)
  const [habitatMapLevels, setHabitatMapLevels] = useState<HabitatMapLevel[]>([]);
  const [currentMapLevel, setCurrentMapLevel] = useState<HabitatMapLevel>({
    name: '',
    id: '',
    centerPoint: [43.63555, -123.56400],
    boundHeight: 0.1,
    hasBeenProcessed: false
  });

  useEffect(() => {
    fetch(BASE_URL+"levels").then(response => response.json()).then(data => {
      console.log(data)
      setHabitatMapLevels(data);
    })
    console.log(bad_data, "bad_data");
  }, []);

  const RunGISProcess = () => {
      fetch('http://127.0.0.1:5000/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        mode: 'cors',
        body: JSON.stringify(currentMapLevel)
      }).then(response => response.json())
      .then(data => {
        console.log(data);
      });
  }
  const GetBounds = (centerPoint: number[], boundHeight: number) => {
    const bounds: LatLngBoundsExpression = [
      [centerPoint[0] - boundHeight, centerPoint[1] - boundHeight / Math.cos(centerPoint[0] * Math.PI/180)] as LatLngTuple,
      [centerPoint[0] + boundHeight, centerPoint[1] + boundHeight / Math.cos(centerPoint[0] * Math.PI/180)] as LatLngTuple
    ]
    return bounds;
  }

  const LocationFinderDummy = () => {
    const map = useMapEvents({
        click(e) {
          if (moveBox) setCurrentMapLevel({
            ...currentMapLevel,
            centerPoint: [e.latlng.lat, e.latlng.lng]
          });
  
        },
    });
    return null;
};

  return (
    <div className='flex flex-col w-full h-full'>
      <div className='flex justify-center items-center w-full h-16 bg-blue-500 text-white'>
        <h1 className='text-2xl font-bold'>Habitat Map Tool</h1>
      </div>
      <div className='flex flex-row w-full h-full'>
        <div className='flex h-full w-96 flex-col space-y-4 p-4'>
          <LevelList levels={habitatMapLevels} setCurrentMapLevel={setCurrentMapLevel} />
        </div>
        <MapContainer className='bg-slate-100' style={{height: 'calc(100vh - 4rem)',width: '100%'}}
        center={currentMapLevel.centerPoint as LatLngExpression } zoom={13} scrollWheelZoom={true}>
          <TileLayer
              eventHandlers={{
                click: (e) => {
                  console.log(e);

                }
              }}  
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url={baseMapsURLs[baseMap as keyof typeof baseMapsURLs]}
          />

          <LocationFinderDummy />
          {habitatMapLevels.map((level) => {
            return (
              <Rectangle bounds={
                GetBounds(level.centerPoint, level.boundHeight)
              } color={ 'gray'
              } weight={1} />
            )
          })}
          <Rectangle bounds={
            GetBounds(currentMapLevel.centerPoint, currentMapLevel.boundHeight)
          } color='blue' weight={1} />

          <Marker 
            position={currentMapLevel.centerPoint as LatLngExpression}
            icon={new Icon({iconUrl: markerIconPng, iconSize: [25, 41], iconAnchor: [12, 41]})}
            >
            <Popup>
              A pretty CSS3 popup. <br /> Easily customizable.
            </Popup>
          </Marker>
          {/* @ts-ignore */}
          <GeoJSON style={{"color": "#343434", "weight": 1, "opacity": 0.95}} data={bad_data} />
        </MapContainer>
        <div className='fixed w-96 p-4 bg-white ' style={{top:'4rem',right:0,zIndex:9999}}>
        <LevelConfig level={currentMapLevel} setLevel={setCurrentMapLevel} moveBox={moveBox} setMoveBox={setMoveBox} RunGISProcess={RunGISProcess} />
        </div>
        <div className="fixed w-96 p-4 bg-white" style={{bottom:0,right:0,zIndex:9999}}>
          <div className="flex flex-col">
            <div className="flex font-bold text-xl">Base Maps</div>
            <select onChange={(e) => {
                setBaseMap(e.target.value);
            }} className='w-full bg-slate-200 p-2'>
              {Object.keys(baseMapsURLs).map((key) => {
                return (
                  <option value={key}>{key}</option>
                )
              })}
            </select>
          </div>
          </div>
      </div>
      

    </div>

  );
}

export default App;
