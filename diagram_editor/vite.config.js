import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'node:fs';
import path from 'node:path';

// Ship the notices of every package that actually contributes code to a chunk.
function notices(){
 return {name:'bundled-license-notices',generateBundle(_,bundle){
  const packages=new Map();
  for(const chunk of Object.values(bundle)){
   if(chunk.type!=='chunk')continue;
   for(const moduleId of Object.keys(chunk.modules)){
    if(!moduleId.includes('/node_modules/'))continue;
    let folder=path.dirname(moduleId.split('?')[0]);
    while(folder.includes('node_modules')){
     const manifest=path.join(folder,'package.json');
     if(fs.existsSync(manifest)){
      const pkg=JSON.parse(fs.readFileSync(manifest,'utf8'));
      if(pkg.name&&!packages.has(pkg.name)){
       const files=fs.readdirSync(folder).filter(n=>/^(licen[cs]e|copying|notice)(\.|$)/i.test(n)&&fs.statSync(path.join(folder,n)).isFile());
       if(!files.length)throw new Error('Missing license notice: '+pkg.name);
       packages.set(pkg.name,pkg.name+' '+pkg.version+' ('+pkg.license+')\n'+files.map(n=>fs.readFileSync(path.join(folder,n),'utf8')).join('\n'));
      }break;
     }folder=path.dirname(folder);
    }
   }
  }
  this.emitFile({type:'asset',fileName:'THIRD_PARTY_NOTICES.txt',source:[...packages.values()].sort().join('\n\n====================\n\n')});
 }};
}
export default defineConfig({
 base:'./',plugins:[react(),notices()],
 build:{outDir:'../flutter_ui/assets/flow_editor',emptyOutDir:true,manifest:'asset-manifest.json'},
});
