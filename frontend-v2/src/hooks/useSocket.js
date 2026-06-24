import { useEffect, useRef } from "react";
import { getSocket } from "../socket";

export function useSocket(event, handler) {
    const socketRef = useRef(null);
    
    useEffect(() => {
        socketRef.current = getSocket();
        const socket = socketRef.current;
        
        socket.on(event, handler);
        
        return () => {
            socket.off(event, handler);
        };
    }, [event, handler]);
}