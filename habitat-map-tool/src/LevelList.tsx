import { HabitatMapLevel } from "./App";

interface LeveListProps {
    levels: HabitatMapLevel[];
    setCurrentMapLevel: (level: HabitatMapLevel) => void;
}
const LevelList = ({levels, setCurrentMapLevel}: LeveListProps) => {
    return (    
        <>       
            <div className="flex font-bold text-xl">Levels</div>
            <div className='flex flex-col space-y-2'>
            {levels.map((level) => {
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


        </>
    )
}
export default LevelList;