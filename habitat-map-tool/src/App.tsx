import React, { useEffect, useState } from 'react';
import logo from './logo.svg';
import './App.css';
import { HiLockClosed, HiLockOpen } from 'react-icons/hi';
import { LatLngBoundsExpression, LatLngExpression, LatLngTuple } from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup, Rectangle, useMapEvents } from 'react-leaflet';
import markerIconPng from "leaflet/dist/images/marker-icon.png"
import {Icon} from 'leaflet'

const BASE_URL = 'http://127.0.0.1:5000/'


interface HabitatMapLevel {
  name: string;
  id: string;
  centerPoint: number[];
  boundHeight: number;
  hasBeenProcessed: boolean;
}


function App() {
  const [moveBox, setMoveBox] = useState<boolean>(true);

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

          <div className="flex font-bold text-xl">Levels</div>
          <div className='flex flex-col space-y-2'>
            {habitatMapLevels.map((level) => {
              return (
                <div className='flex flex-row justify-between items-center bg-slate-200 p-2 rounded-md'>
                  <div className='flex flex-col'>
                    <div className='font-bold'>{level.name}</div>
                    <div className='text-sm'>{level.centerPoint[0]}, {level.centerPoint[1]}</div>
                  </div>
                  <button onClick={()=>{
                    setCurrentMapLevel(level);
                  }} className='bg-blue-500 text-white p-2 rounded-md'>View</button>
                </div>
              )
            })}
          </div>


          <div className="flex font-bold text-xl">Level Configuration</div>
          <div className="flex flex-col">
            <div className="flex font-bold">Level Name</div>
            <div className='flex flex-row justify-between items-center py-2'>  
              <input className='w-full bg-slate-200 p-2' type='text' value={currentMapLevel.name} onChange={(e) =>
                setCurrentMapLevel({
                  ...currentMapLevel,
                  name: e.target.value
                })
              } />
            </div>
          </div>
          <div className="flex flex-col">
            <div className="flex font-bold">Center Point</div>
            <div className='flex flex-row justify-between items-center'>
              <div className="">{currentMapLevel.centerPoint[0]}, {currentMapLevel.centerPoint[1]}</div>
              <button onClick={() => setMoveBox(!moveBox)} className={(moveBox ? 'bg-blue-500' : 'bg-slate-500') + ' text-white p-2 ml-auto p-2 flex items-center justify-center rounded-md'}>
                {moveBox ? <HiLockOpen className='w-8 h-8'/> : <HiLockClosed className='w-8 h-8'/>}
              </button>

            </div>
          </div>

          <div className="flex flex-col">
            <div className="flex font-bold">Bounding Box Height (°)</div>
            <div className='flex flex-row justify-between items-center py-2'>
              <input className='w-20 bg-slate-200 p-2' type='number' value={currentMapLevel.boundHeight} onChange={(e) =>
                setCurrentMapLevel({
                  ...currentMapLevel,
                  boundHeight: parseFloat(e.target.value)
                })
              }/>
              <div className='flex'>({currentMapLevel.boundHeight * 69} mi)</div>
            </div>
          </div>
          <div className="flex flex-col">
              <button onClick={RunGISProcess} className='bg-blue-500 text-white p-2 rounded-md'>Run GIS Process</button>
          </div>
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
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
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
        </MapContainer>
      </div>
      

    </div>

  );
}

export default App;
