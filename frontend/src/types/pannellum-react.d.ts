declare module 'pannellum-react' {
    import { Component } from 'react';

    export interface PannellumProps {
        image: string;
        width?: string;
        height?: string;
        autoLoad?: boolean;
        showZoomCtrl?: boolean;
        mouseZoom?: boolean;
        showFullscreenCtrl?: boolean;
        autoRotate?: number;
        pitch?: number;
        yaw?: number;
        hfov?: number;
        minHfov?: number;
        maxHfov?: number;
        compass?: boolean;
        northOffset?: number;
        preview?: string;
        previewTitle?: string;
        previewAuthor?: string;
        author?: string;
        title?: string;
        orientationOnByDefault?: boolean;
        draggable?: boolean;
        disableKeyboardCtrl?: boolean;
        showControls?: boolean;
        onLoad?: () => void;
        onScenechange?: (sceneId: string) => void;
        onScenechangefadedone?: () => void;
        onError?: (error: any) => void;
        onErrorcleared?: () => void;
        onMousedown?: (event: any) => void;
        onMouseup?: (event: any) => void;
        onTouchstart?: (event: any) => void;
        onTouchend?: (event: any) => void;
        hotspotDebug?: boolean;
        hotSpots?: any[];
        [key: string]: any;
    }

    export class Pannellum extends Component<PannellumProps> {}
}
