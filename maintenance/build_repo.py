#!/usr/bin/env python3
"""Build sahinkaa's flat APT repository without changing executable payloads."""
from pathlib import Path
import argparse,base64,bz2,copy,datetime,email.utils,gzip,hashlib,html,io,json,lzma,re,shutil,tarfile
ROOT=Path(__file__).resolve().parent
SITE=ROOT.parent if ROOT.name=='maintenance' else ROOT/'site'
URL='https://sahinkaa.github.io/'
ARCHES=('iphoneos-arm64e','iphoneos-arm64')
def ar_read(raw):
    if raw[:8]!=b'!<arch>\n':raise ValueError('Invalid Debian archive')
    pos=8;items=[]
    while pos<len(raw):
        h=raw[pos:pos+60]
        if len(h)!=60 or h[58:]!=b'`\n':raise ValueError('Invalid ar header')
        size=int(h[48:58]);data=raw[pos+60:pos+60+size]
        if len(data)!=size:raise ValueError('Truncated ar member')
        items.append((h[:16].decode().strip().rstrip('/'),h,data));pos+=60+size+(size%2)
    if pos!=len(raw):raise ValueError('Bad archive padding')
    return items
def ar_write(items):
    out=bytearray(b'!<arch>\n')
    for name,h,data in items:
        out.extend(h[:48]+str(len(data)).encode().ljust(10)+h[58:]);out.extend(data)
        if len(data)%2:out.extend(b'\n')
    return bytes(out)
def fields(text):
    out={};key=None
    for line in text.splitlines():
        if line.startswith((' ','\t')):
            if not key:raise ValueError('Continuation without field')
            out[key]+='\n'+line
        elif line:
            key,value=line.split(':',1)
            if key in out:raise ValueError('Duplicate control field')
            out[key]=value.strip()
    return out
def serialize(f):return ''.join(k+': '+v+'\n' for k,v in f.items())
def control_member(items):
    return next((n,h,d) for n,h,d in items if n.startswith('control.tar'))
def tar_members(raw):
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as t:
        return [(copy.copy(m),t.extractfile(m).read() if m.isfile() else None) for m in t.getmembers()]
def control_fields(items):
    for m,d in tar_members(control_member(items)[2]):
        if m.name.lstrip('./')=='control':return fields(d.decode('utf-8'))
    raise ValueError('No control file')
def change_control(items,newfields):
    name,header,raw=control_member(items);out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w',format=tarfile.GNU_FORMAT) as t:
        for m,d in tar_members(raw):
            if m.name.lstrip('./')=='control':d=serialize(newfields).encode();m.size=len(d)
            t.addfile(m,io.BytesIO(d) if d is not None else None)
    raw=out.getvalue()
    if name.endswith('.gz'):raw=gzip.compress(raw,mtime=0)
    elif name.endswith('.xz'):raw=lzma.compress(raw)
    elif name.endswith('.bz2'):raw=bz2.compress(raw)
    elif name!='control.tar':raise ValueError('Unsupported control compression')
    return ar_write([(n,h,raw if n==name else d) for n,h,d in items])
def digest(raw,algo='sha256'):return hashlib.new(algo,raw).hexdigest()
def original_icon(items):
    data=next(d for n,h,d in items if n.startswith('data.tar'))
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as t:
        candidates=[m for m in t.getmembers() if m.isfile() and re.search(r'/PreferenceBundles/[^/]+\.bundle/(?:icon|Icon)(?:@[23]x)?\.png$',m.name)]
        candidates.sort(key=lambda m:('@3x' not in m.name,'@2x' not in m.name,m.name))
        return t.extractfile(candidates[0]).read() if candidates else None
CSS='''*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#0b0b0d;color:#eeeef0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit}main{max-width:1000px;margin:auto;padding:48px 24px 60px}.brand{display:flex;align-items:center;gap:16px}.brand img{width:64px;height:64px;border:1px solid #333337;border-radius:17px}.brand h1{margin:0;font-size:30px;letter-spacing:-1px}.intro{margin:42px 0 34px;max-width:690px}.intro h2{font-size:clamp(30px,6vw,46px);letter-spacing:-1.4px;line-height:1.12;margin:0 0 16px}.muted{color:#a9a9b2}.actions{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:10px 20px;border:1px solid #3a3a40;border-radius:12px;text-decoration:none;font-weight:600;background:#19191d}.btn.primary{background:#f3f3f5;color:#111;border-color:#f3f3f5}.address{display:flex;gap:12px;align-items:center;flex-wrap:wrap}code{font:14px ui-monospace,SFMono-Regular,monospace;overflow-wrap:anywhere}.address code{background:#19191d;padding:10px 14px;border-radius:10px}button{font:inherit;color:inherit;cursor:pointer}.summary{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid #28282e;padding-bottom:14px;margin:44px 0 20px}.summary h2{font-size:22px;margin:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{background:#151518;border:1px solid #2a2a30;border-radius:18px;padding:22px;text-decoration:none;display:block;transition:border-color .15s}.card:hover{border-color:#6b6b77}.cardhead{display:flex;gap:14px;align-items:center}.card img{width:48px;height:48px;border-radius:12px;border:1px solid #36363c;object-fit:cover}.card h3{font-size:17px;line-height:1.3;margin:0 0 4px}.version{font-size:13px;color:#a4a4ad}.card p{margin:16px 0;color:#c5c5cc;font-size:14px}.tags{display:flex;gap:7px;flex-wrap:wrap}.tag{font-size:12px;padding:4px 9px;border:1px solid #393940;border-radius:99px}.tag.os{color:#b7d7fc;border-color:#35485b;background:#17212c}footer{margin-top:40px;padding-top:24px;border-top:1px solid #28282e;color:#a4a4ad;font-size:13px}.detail{max-width:760px}.detail h1{font-size:32px;line-height:1.2}.detail section{padding:18px 0;border-top:1px solid #28282e}.detail h2{font-size:18px;margin:0 0 12px}.detail p{margin:10px 0}.detail .downloads{display:flex;gap:10px;flex-wrap:wrap}.detail ul{padding-left:22px}@media(max-width:640px){main{padding:28px 18px 40px}.grid{grid-template-columns:1fr}.intro{margin-top:32px}.card{padding:19px}.summary{margin-top:34px}.summary span{font-size:13px}.btn{flex:1}.detail .btn{flex:initial}}@media(prefers-reduced-motion:reduce){*{transition:none!important}}'''
def page(title,body,desc='Jailbreak tweaks from sahinkaa. Add this repository to Sileo or Zebra.'):
    return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><meta name="description" content="'+html.escape(desc,quote=True)+'"><meta name="theme-color" content="#0b0b0d"><link rel="icon" href="/CydiaIcon.png"><link rel="stylesheet" href="/assets/style.css"></head><body>'+body+'</body></html>\n'
def build():
    SITE.mkdir(exist_ok=True);(SITE/'debs').mkdir(exist_ok=True);(SITE/'depictions').mkdir(exist_ok=True);(SITE/'assets/icons').mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'compatibility.json').read_text());packages=[];audit=[]
    for item in json.loads((ROOT/'packages-inventory.json').read_text()):
        original=ROOT/'original-debs'/item['asset']['name']
        if not original.exists():
            import urllib.request
            original.parent.mkdir(exist_ok=True)
            request=urllib.request.Request(item['asset']['browser_download_url'],headers={'User-Agent':'sahinkaa-repository-builder'})
            with urllib.request.urlopen(request,timeout=60) as response:download=response.read()
            if digest(download)!=item['sha256']:raise ValueError('Upstream release checksum changed')
            original.write_bytes(download)
        raw=original.read_bytes();assert digest(raw)==item['sha256']
        members=ar_read(raw);old=control_fields(members);f=dict(old);repo=item['repository'];identifier=f['Package'];compat=config[repo]
        assert f['Architecture'] in ARCHES
        # Keep source credits unless this repository has an explicit credit correction.
        if compat.get('author'):f['Author']=compat['author']
        # Enrich only descriptions missing iOS information, keeping source compatibility claims.
        if compat.get('description'):f['Description']=compat['description']
        elif not re.search(r'\biOS\s*(?:/\s*iPadOS\s*)?\d|\biPadOS\s*\d',f.get('Description',''),re.I):f['Description']=f['Description'].rstrip()+f' {compat["ios"]}.'
        slug=identifier
        icon=original_icon(members)
        if icon:(SITE/'assets/icons'/f'{slug}.png').write_bytes(icon)
        f['Icon']=URL+(f'assets/icons/{slug}.png' if icon else 'CydiaIcon.png')
        f['Homepage']=f'https://github.com/sahinkaa/{repo}'
        f['Depiction']=URL+f'depictions/{slug}.html'
        f['SileoDepiction']=URL+f'depictions/{slug}.json'
        updated=change_control(members,f)
        check=ar_read(updated);assert control_fields(check)==f
        # Archive payload, signature-bearing Mach-O files and maintainer scripts stay byte-identical.
        assert [(n,d) for n,h,d in members if not n.startswith('control.tar')]==[(n,d) for n,h,d in check if not n.startswith('control.tar')]
        before=tar_members(control_member(members)[2]);after=tar_members(control_member(check)[2])
        assert [(m.name,d,m.mode,m.uid,m.gid,m.linkname) for m,d in before if m.name.lstrip('./')!='control']==[(m.name,d,m.mode,m.uid,m.gid,m.linkname) for m,d in after if m.name.lstrip('./')!='control']
        assert all(f[k]==old[k] for k in old if k not in ['Description','Icon','Homepage','Depiction','SileoDepiction','Author'])
        (SITE/'debs'/item['asset']['name']).write_bytes(updated)
        stanza=dict(f);stanza.update({'Filename':'debs/'+item['asset']['name'],'Size':str(len(updated)),'MD5sum':digest(updated,'md5'),'SHA1':digest(updated,'sha1'),'SHA256':digest(updated),'SHA512':digest(updated,'sha512')})
        packages.append(stanza)
        audit.append({'repository':repo,'package':identifier,'name':f['Name'],'version':f['Version'],'architecture':f['Architecture'],'filename':item['asset']['name'],'source_release':item['release'],'original_sha256':digest(raw),'sha256':digest(updated),'payload_unchanged':True,'maintainer_scripts_unchanged':True,'dependencies_unchanged':True,'changed_fields':[k for k in f if f.get(k)!=old.get(k)],'compatibility':compat['compatibility'],'ios':compat['ios'],'description':f['Description'],'author':f.get('Author','sahinkaa'),'icon':f['Icon']})
        if compat.get('changelog'):audit[-1]['changelog']=compat['changelog']
    # Native RootHide comes first for clients which also allow rootless as a foreign architecture.
    packages.sort(key=lambda f:(ARCHES.index(f['Architecture']),f['Package']))
    data=('\n'.join(serialize(p) for p in packages)+'\n').encode()
    write_indexes(SITE,data)
    # Optional standard suite for advanced APT clients; root URL remains a flat source.
    suite=SITE/'dists/stable';all_index=[]
    for arch in ARCHES:
        folder=suite/'main'/('binary-'+arch);folder.mkdir(parents=True,exist_ok=True)
        selected=('\n'.join(serialize(p) for p in packages if p['Architecture']==arch)+'\n').encode();write_indexes(folder,selected,release=False)
        for f in sorted(folder.glob('Packages*')):all_index.append((f.relative_to(suite).as_posix(),f.read_bytes()))
    (suite/'Release').write_text(release(all_index,components=True))
    catalog=[]
    for identifier in sorted(set(a['package'] for a in audit),key=lambda i:next(a['name'].lower() for a in audit if a['package']==i)):
        entries=[a for a in audit if a['package']==identifier];a=entries[0];a=dict(a,architectures=[x['architecture'] for x in entries],downloads=[{'architecture':x['architecture'],'filename':x['filename']} for x in entries]);catalog.append(a)
        render_depiction(a, config[a['repository']].get('screenshots', ()))
    (SITE/'assets/style.css').write_text(CSS)
    cards=''.join('<a class="card" href="/depictions/'+a['package']+'.html"><div class="cardhead"><img src="'+html.escape(a['icon'].replace(URL,'/'),quote=True)+'" alt="" loading="lazy"><div><h3>'+html.escape(a['name'])+'</h3><div class="version">'+html.escape(a['version'])+'</div></div></div><p>'+html.escape(a['description'])+'</p><div class="tags"><span class="tag os">'+html.escape(a['ios'])+'</span><span class="tag">Rootless</span>'+('<span class="tag">RootHide</span>' if 'iphoneos-arm64e' in a['architectures'] else '')+'</div></a>' for a in catalog)
    body='''<main><header class="brand"><img src="/assets/profile.png" alt="sahinkaa GitHub profile picture"><h1>sahinkaa</h1></header><section class="intro"><h2>Tweaks for your jailbreak.</h2><p class="muted">Add one source. Your package manager selects the build for your jailbreak. Each tweak lists its supported iOS versions.</p><div class="actions"><a class="btn primary" href="sileo://source/https://sahinkaa.github.io/">Add to Sileo</a><a class="btn" href="zbra://sources/add/https://sahinkaa.github.io/">Add to Zebra</a></div><div class="address"><code>https://sahinkaa.github.io/</code><button class="btn" id="copy-address" type="button">Copy address</button><span id="copy-status" role="status" aria-live="polite"></span></div></section><div class="summary"><h2>All tweaks</h2><span class="muted">11 tweaks · 20 packages</span></div><div class="grid">'''+cards+'''</div><footer><p>Rootless and native RootHide builds share the same package identity and version. Rootless-only releases are marked above. Native RootHide packages install directly without Patcher.</p><p>Compatibility reflects each project's published requirements. A supported range does not mean every device and OS version has been tested.</p><a href="https://github.com/sahinkaa">GitHub</a> · <a href="https://github.com/sahinkaa/sahinkaa.github.io">Repository source</a></footer></main><script src="/assets/site.js" defer></script>'''
    (SITE/'index.html').write_text(page('sahinkaa',body))
    (SITE/'assets/site.js').write_text("document.querySelector('#copy-address')?.addEventListener('click',async()=>{const status=document.querySelector('#copy-status');try{await navigator.clipboard.writeText('https://sahinkaa.github.io/');status.textContent='Copied';}catch{status.textContent='Select and copy the address above.';}});\n")
    (SITE/'.nojekyll').write_text('')
    (SITE/'robots.txt').write_text('User-agent: *\nAllow: /\n')
    (SITE/'packages.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (ROOT/'metadata-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    (SITE/'metadata-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    (SITE/'SHA256SUMS').write_text(''.join(digest(f.read_bytes())+'  '+f.relative_to(SITE).as_posix()+'\n' for f in sorted((SITE/'debs').glob('*.deb'))))
    (SITE/'README.md').write_text('''# sahinkaa

APT repository: **https://sahinkaa.github.io/**

Add the URL to Sileo or Zebra. Repository label: **sahinkaa**. The icon is the account's GitHub profile picture.

The root is a flat Debian repository. Both flat and suite Release files include `Components: main`, which Sileo requires even for flat sources. `Release` advertises `iphoneos-arm64` (rootless) and `iphoneos-arm64e` (native RootHide). `Packages` contains separate entries for both builds with the original package IDs and unchanged versions. Current clients select by their jailbreak's package architecture, not the phone CPU name. RootHide requires a RootHide-aware package manager.

There are eleven released tweaks and twenty packages. Two projects have only rootless releases and are distributed as rootless only. The repository does not relabel or convert those packages. A native RootHide release can be added later after it is built and tested.

Each package has an HTML depiction for Zebra and a native JSON depiction for Sileo, with compatibility information and links to its original project. GitHub release assets remain unchanged. Repository copies add compatibility text when missing, HTTP icons and depiction links. Versions, dependencies, maintainer scripts and executable payloads are preserved. `metadata-audit.json` records original/repository checksums and changed fields.

`Packages`, `.gz`, `.bz2` and `.xz` variants and their Release hashes are generated together. An optional `dists/stable/main/binary-<architecture>` layout is also provided. The normal source URL uses the flat index. This is an unsigned HTTPS repository, as is common for jailbreak sources; no private signing key is included.

## Updating

Only add published packages belonging to this account. Keep genuine rootless and RootHide builds separate. Preserve `Package`, `Version`, `Architecture` and dependency requirements. Refresh all package sizes and hashes whenever a .deb changes, then regenerate compressed indexes and Release hashes. Do not edit a .deb after indexing it.

The reproducible builder is `maintenance/build_repo.py`, with pinned source-release checksums and compatibility data alongside it. Run `python3 maintenance/build_repo.py` from a clone to rebuild, or `python3 maintenance/build_repo.py --verify` to check the committed repository without downloading anything. The builder verifies that metadata changes preserve the complete data archive and non-control maintainer files. Downloaded upstream .debs are stored outside the published repository.

Package licenses and original developer credits remain in each package and source project. See each tweak's project for its license and device-testing details.
''')
    print('Built',len(catalog),'tweaks and',len(packages),'packages.')
def write_indexes(folder,data,release=True):
    variants={'Packages':data,'Packages.gz':gzip.compress(data,mtime=0),'Packages.bz2':bz2.compress(data),'Packages.xz':lzma.compress(data)}
    for name,raw in variants.items():(folder/name).write_bytes(raw)
    if release:(folder/'Release').write_text(globals()['release'](list(variants.items())))
def release(entries,components=False):
    out='Origin: sahinkaa\nLabel: sahinkaa\nSuite: stable\nCodename: sahinkaa\nVersion: 1.0\nArchitectures: iphoneos-arm64 iphoneos-arm64e\n'
    # Sileo requires Components even for a flat source.
    out+='Components: main\n'
    out+='Description: Jailbreak tweaks from sahinkaa\nIcon: '+URL+'CydiaIcon.png\nDate: '+email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc),usegmt=True)+'\n'
    for label,algo in [('MD5Sum','md5'),('SHA1','sha1'),('SHA256','sha256'),('SHA512','sha512')]:
        out+=label+':\n'+''.join(' '+digest(raw,algo)+' '+str(len(raw))+' '+name+'\n' for name,raw in entries)
    return out
def render_depiction(a, screenshots=()):
    name=a['name'];slug=a['package'];hasrh='iphoneos-arm64e' in a['architectures'];env='Rootless and native RootHide' if hasrh else 'Rootless only'
    links=''.join('<a class="btn" href="/debs/'+html.escape(d['filename'],quote=True)+'">'+('RootHide' if d['architecture']=='iphoneos-arm64e' else 'Rootless')+' .deb</a>' for d in a['downloads'])
    body='<main class="detail"><a class="muted" href="/">← sahinkaa</a><div class="cardhead" style="margin-top:30px"><img src="'+a['icon'].replace(URL,'/')+'" alt="" width="64" height="64"><h1>'+html.escape(name)+'</h1></div><p>'+html.escape(a['description'])+'</p><div class="tags"><span class="tag os">'+a['ios']+'</span><span class="tag">'+env+'</span><span class="tag">'+a['version']+'</span></div><section style="margin-top:28px"><h2>Compatibility</h2><p>'+html.escape(a['compatibility'])+'</p><p>'+('Install the native RootHide package directly without converting the rootless package.' if hasrh else 'Only the published rootless build is hosted. This is not a native RootHide package.')+'</p></section><section><h2>Developer</h2><p>'+html.escape(a['author'])+'</p></section><section><h2>Download</h2><div class="downloads">'+links+'</div><p class="muted">When installed through Sileo or Zebra, your package manager chooses the matching architecture.</p></section><footer><a href="https://github.com/sahinkaa/'+a['repository']+'">Source and instructions</a> · <a href="'+a['source_release']+'">GitHub release</a></footer></main>'
    if screenshots:
        tiles=[]
        for screenshot in screenshots:
            image=html.escape(screenshot['url'], quote=True)
            alt=html.escape(screenshot['accessibilityText'], quote=True)
            tiles.append(f'<a href="{image}"><img src="{image}" alt="{alt}" width="1242" height="2688" loading="lazy" style="display:block;width:100%;height:auto;border-radius:12px"></a>')
        gallery='<section><h2>Screenshots</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,160px),1fr));gap:12px">' + ''.join(tiles) + '</div></section>'
        body=body.replace('<section style="margin-top:28px"><h2>Compatibility</h2>', gallery + '<section><h2>Compatibility</h2>', 1)
    history=a.get('changelog',[])
    if history:
        sections=''.join('<h3>'+html.escape(entry['version'])+' <span class="muted">'+html.escape(entry['date'])+'</span></h3><ul>'+''.join('<li>'+html.escape(change)+'</li>' for change in entry['changes'])+'</ul>' for entry in history)
        body=body.replace('<section><h2>Developer</h2>','<section><h2>Changelog</h2>'+sections+'</section><section><h2>Developer</h2>',1)
    (SITE/'depictions'/f'{slug}.html').write_text(page(name+' - sahinkaa',body,a['description']))
    views=[{'class':'DepictionHeaderView','title':name,'useBoldText':True}, {'class':'DepictionMarkdownView','markdown':a['description'],'useSpacing':True}, {'class':'DepictionHeaderView','title':'Compatibility'}, {'class':'DepictionMarkdownView','markdown':a['compatibility']+'\n\n'+env+'.'+ (' Native RootHide installs directly without Patcher.' if hasrh else ''),'useSpacing':True}, {'class':'DepictionTableTextView','title':'Version','text':a['version']}, {'class':'DepictionTableTextView','title':'Developer','text':a['author']}, {'class':'DepictionButtonView','text':'Source and instructions','action':'https://github.com/sahinkaa/'+a['repository']}, {'class':'DepictionButtonView','text':'GitHub release','action':a['source_release']}]
    if screenshots:
        views[2:2]=[
            {'class':'DepictionHeaderView','title':'Screenshots'},
            {'class':'DepictionScreenshotsView','itemSize':'{155, 335}','itemCornerRadius':12,
             'screenshots':list(screenshots)}
        ]
    tabs=[{'class':'DepictionStackView','tabname':'Details','views':views}]
    if history:
        history_views=[]
        for entry in history:
            history_views.extend([{'class':'DepictionHeaderView','title':entry['version']+(' - '+entry['date'] if entry.get('date') else '')},{'class':'DepictionMarkdownView','markdown':'\n'.join('- '+change for change in entry['changes']),'useSpacing':True}])
        tabs.append({'class':'DepictionStackView','tabname':'Changelog','views':history_views})
    (SITE/'depictions'/f'{slug}.json').write_text(json.dumps({'class':'DepictionTabView','minVersion':'0.4','tabs':tabs},indent=2)+'\n')
def verify():
    raw=(SITE/'Packages').read_bytes();packages=[fields(x) for x in raw.decode().strip().split('\n\n')]
    assert len(packages)==20 and len({p['Package'] for p in packages})==11
    assert gzip.decompress((SITE/'Packages.gz').read_bytes())==raw and bz2.decompress((SITE/'Packages.bz2').read_bytes())==raw and lzma.decompress((SITE/'Packages.xz').read_bytes())==raw
    for p in packages:
        data=(SITE/p['Filename']).read_bytes();f=control_fields(ar_read(data));assert all(f[k]==p[k] for k in f)
        assert p['Size']==str(len(data))
        for label,algo in [('MD5sum','md5'),('SHA1','sha1'),('SHA256','sha256'),('SHA512','sha512')]:assert p[label]==digest(data,algo)
        assert p['Architecture'] in ARCHES
        assert p['Author'].split(' • ').count('sahinkaa')==1
        if p['Package']=='com.sahinkaa.neverlowermusic16':assert p['Author']=='Rishanan • sahinkaa'
        assert re.search(r'\biOS\s*(?:/\s*iPadOS\s*)?\d|\biPadOS\s*\d',p['Description'],re.I)
        for key in ['Depiction','SileoDepiction','Icon']:assert p[key].startswith(URL) and (SITE/p[key][len(URL):]).is_file()
    for r in [SITE/'Release',SITE/'dists/stable/Release']:
        f=fields(r.read_text());assert f['Origin']==f['Label']=='sahinkaa' and set(f['Architectures'].split())==set(ARCHES)
        assert f.get('Components')=='main', 'Sileo requires Components in every Release file'
        for label,algo in [('MD5Sum','md5'),('SHA1','sha1'),('SHA256','sha256'),('SHA512','sha512')]:
            for line in f[label].splitlines():
                if not line.strip():continue
                sha,size,name=line.split();data=(r.parent/name).read_bytes();assert digest(data,algo)==sha and len(data)==int(size)
    for arch,count in [('iphoneos-arm64',11),('iphoneos-arm64e',9)]:
        d=(SITE/f'dists/stable/main/binary-{arch}/Packages').read_bytes();entries=[fields(x) for x in d.decode().strip().split('\n\n')];assert len(entries)==count and all(p['Architecture']==arch for p in entries)
    for p in (SITE/'depictions').glob('*.json'):assert json.loads(p.read_text())['class']=='DepictionTabView'
    assert all(x['payload_unchanged'] and x['maintainer_scripts_unchanged'] and x['dependencies_unchanged'] for x in json.loads((SITE/'metadata-audit.json').read_text()))
    print('PASS: package controls, unchanged payload audit, all hashes, compression variants, 11 rootless/9 RootHide entries and depictions.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    if args.verify:verify()
    else:build();verify()
