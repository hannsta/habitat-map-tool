import { HiLockOpen, HiLockClosed } from "react-icons/hi";
import { HabitatMapLevel } from "./App";

interface LevelConfigProps {
    level: HabitatMapLevel;
    setLevel: (level: HabitatMapLevel) => void;
    moveBox: boolean;
    setMoveBox: (moveBox: boolean) => void;
    RunGISProcess: () => void;
}

const LevelConfig = ({level, setLevel, moveBox, setMoveBox, RunGISProcess}: LevelConfigProps) => {
    return (
        <div className="flex flex-col space-y-4">
        <div className="flex font-bold text-xl">Level Configuration</div>
          <div className="flex flex-col">
            <div className="flex font-bold">Level Name</div>
            <div className='flex flex-row justify-between items-center py-2'>  
              <input className='w-full bg-slate-200 p-2' type='text' value={level.name} onChange={(e) =>
                setLevel({
                  ...level,
                  name: e.target.value
                })
              } />
            </div>
          </div>
          <div className="flex flex-col">
            <div className="flex font-bold">Center Point</div>
            <div className='flex flex-row justify-between items-center'>
              <div className="">{level.centerPoint[0]}, {level.centerPoint[1]}</div>
              <button onClick={() => setMoveBox(!moveBox)} className={(moveBox ? 'bg-blue-500' : 'bg-slate-500') + ' text-white p-2 ml-auto p-2 flex items-center justify-center rounded-md'}>
                {moveBox ? <HiLockOpen className='w-8 h-8'/> : <HiLockClosed className='w-8 h-8'/>}
              </button>

            </div>
          </div>

          <div className="flex flex-col">
            <div className="flex font-bold">Bounding Box Height (°)</div>
            <div className='flex flex-row justify-between items-center py-2'>
              <input className='w-20 bg-slate-200 p-2' type='number' value={level.boundHeight} onChange={(e) =>
                setLevel({
                  ...level,
                  boundHeight: parseFloat(e.target.value)
                })
              }/>
              <div className='flex'>({level.boundHeight * 69} mi)</div>
            </div>
          </div>
          <div className="flex flex-col">
              <button onClick={RunGISProcess} className='bg-blue-500 text-white p-2 rounded-md'>Run GIS Process</button>
          </div>
          </div>
    )
}
export default LevelConfig;