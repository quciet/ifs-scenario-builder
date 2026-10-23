"""Local reference preflight and compact, complete metadata for AI planning."""
import difflib
import json
import re
from scenario_intelligence import details, RULES, NARRATIVE_TERMS


def preflight(text, refs, definitions):
    # Exact installed identifiers are safe to preload even in unparenthesized
    # follow-ups. Similar spellings remain suggestions requiring a user choice.
    names = set(re.findall(r'\b[a-z][a-z0-9_]*\b',text)) & refs.parameters.keys()
    conflicts = []
    for match in re.finditer(r'\(([^()]{1,240})\)|`([a-z][a-z0-9_]*)`', text):
        words = re.findall(r'\b[a-z][a-z0-9_]*\b', match.group(1) or match.group(2))
        words = [w for w in words if w not in ('and', 'or', 'with')]
        if not words or not all(w in refs.parameters or '_' in w or (len(w)>4 and w.endswith(('m','add'))) for w in words):
            continue
        names.update(words)
        clause = re.split(r'[.,;\n]', text[:match.start()])[-1].casefold()
        for code in words:
            if code not in RULES: continue
            for other, rule in RULES.items():
                if other == code or other in words or other not in refs.parameters: continue
                terms = NARRATIVE_TERMS.get(other, (rule[0],))
                if any(re.search(r'\b'+re.escape(term)+r'\b', clause) for term in terms):
                    # Only flag an immediately adjacent, explicitly labelled meaning.
                    if any(re.search(re.escape(term)+r'\s*$', clause) for term in terms):
                        conflicts.append({'code':code,'definition':definitions.get(code,''),
                                          'candidate':other,'candidate_definition':definitions.get(other,'')})
    verified = {}
    missing = []
    for name in sorted(names):
        if name in refs.parameters:
            verified[name] = metadata(name, refs, definitions)
        else:
            candidates = difflib.get_close_matches(name, [n for n in refs.parameters if n==n.lower()], n=3, cutoff=.75)
            missing.append({'requested':name,'candidates':[{'name':n,'definition':definitions.get(n,'')} for n in candidates]})
    return {'verified':verified,'missing':missing,'meaning_conflicts':conflicts}


def metadata(name, refs, definitions):
    flags=refs.dimensions(name)
    return {'parameter':name,'definition':definitions.get(name),'dimensions':flags,
            'groups':{f:refs.groups.get(f,{}) for axis,f in enumerate(flags) if f>1 or (axis>0 and f==1)},
            'country_reference':'model_context.country_names' if flags[0]==1 else None,
            'interpretation':details(refs,name)}


def clarification(facts):
    lines=['Before planning the changes, please resolve these checks against the selected IFs installation:']
    for item in facts['missing']:
        text=item['requested']+' is not an installed parameter.'
        if item['candidates']:
            text+=' Possible spelling matches: '+ '; '.join(c['name']+' — '+c['definition'] for c in item['candidates'])+'. Please choose; none has been substituted.'
        else:text+=' Which installed control should represent this change? I will not invent a proxy.'
        lines.append(text)
    for item in facts['meaning_conflicts']:
        lines.append(item['code']+' means '+item['definition']+'. Did you intend '+item['candidate']+' ('+item['candidate_definition']+') for this part of the request?')
    lines.append('The rest of your request is saved. No draft has been created or approved.')
    return '\n\n'.join(lines)


def provider_view(messages):
    """Keep canonical countries once; retain semantic rules and dimension indices."""
    result=[]
    for message in messages:
        item={k:v for k,v in message.items() if not k.startswith('_')}
        if item.get('role')=='tool':
            try:
                data=json.loads(item['content'])
                if isinstance(data,dict) and isinstance(data.get('suggestions'),list):
                    groups={}
                    for row in data['suggestions']:
                        if not isinstance(row,dict):continue
                        values={k:v for k,v in row.items() if k not in ('targets','source','parameter')}
                        key=json.dumps(values,sort_keys=True)
                        group=groups.setdefault(key,{**values,'targets':[]})
                        group['targets'].append(row.get('targets',[]))
                    data={k:v for k,v in data.items() if k!='suggestions'}|{'suggestion_groups':list(groups.values()),
                        'note':'Each group shares the listed baseline and endpoint. All target coordinates are retained.'}
                    item['content']=json.dumps(data)
                if isinstance(data,dict) and 'parameter' in data and 'dimensions' in data and 'countries' in data:
                    data={k:v for k,v in data.items() if k!='countries'}
                    data['country_reference']='model_context.country_names'
                    item['content']=json.dumps(data)
            except (ValueError,TypeError):pass
        result.append(item)
    return result


def numeric_clarification_issue(reply, narrative, refs):
    """New decimal/percentage assumptions beside a multiplier need a validated proposal."""
    for name in set(re.findall(r'\b[a-z][a-z0-9_]*\b',reply)) & refs.parameters.keys():
        if 'mul' not in str(refs.metadata.get(name,{}).get('UNITS','')).casefold():continue
        match=re.search(r'\b'+re.escape(name)+r'\b[^\n?!]{0,60}?([+-]?\d+\.\d+|\d+(?:\.\d+)?\s*%)',reply)
        if match and not re.search(r'(?<!\d)'+re.escape(match[1])+r'(?!\d)',narrative):
            return {'kind':'unvalidated_numeric_assumption','parameter':name,
                    'message':'New numeric assumptions for '+name+' must be in a complete proposal for local validation, not in unvalidated clarification prose.'}
    return None
