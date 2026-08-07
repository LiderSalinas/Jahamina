import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {name:"Jahamina",short_name:"Jahamina",description:"Viajes compartidos dentro de Paraguay",start_url:"/",scope:"/",display:"standalone",background_color:"#f7faf8",theme_color:"#075b49",icons:[{src:"/icons/jahamina.svg",sizes:"any",type:"image/svg+xml",purpose:"maskable"}]};
}
