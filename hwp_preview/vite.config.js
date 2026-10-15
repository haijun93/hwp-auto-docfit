import {defineConfig} from 'vite';
import fs from 'node:fs';
import path from 'node:path';

// rhwp(@rhwp/core, MIT)와 그 안에 WASM으로 들어간 Rust 크레이트 사용권 고지를 함께 싣는다.
function notices(){
 return {name:'rhwp-license-notices',generateBundle(){
  const root=path.resolve('node_modules/@rhwp/core');
  const pkg=JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8'));
  const readme=fs.readFileSync(path.join(root,'README.md'),'utf8');
  const thirdParty=readme.includes('## Third-Party Licenses')?readme.slice(readme.indexOf('## Third-Party Licenses')):'';
  if(!fs.existsSync(path.join(root,'LICENSE')))throw new Error('Missing license notice: @rhwp/core');
  this.emitFile({type:'asset',fileName:'THIRD_PARTY_NOTICES.txt',
   source:`${pkg.name} ${pkg.version} (${pkg.license}) — https://github.com/edwardkim/rhwp\n${fs.readFileSync(path.join(root,'LICENSE'),'utf8')}\n\n${thirdParty}`});
 }};
}
export default defineConfig({
 base:'./',plugins:[notices()],
 build:{outDir:'../flutter_ui/assets/hwp_preview',emptyOutDir:true,manifest:'asset-manifest.json',assetsInlineLimit:0,
  // WASM(약 12MB)은 고정 이름으로 둬서 다시 빌드해도 같은 파일이 되게 한다(저장소가 불어나지 않게).
  rollupOptions:{output:{assetFileNames:a=>(a.names?.[0]??a.name??'').endsWith('.wasm')?'assets/[name][extname]':'assets/[name]-[hash][extname]'}}},
});
