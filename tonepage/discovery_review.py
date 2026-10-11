"""Manual sequence boundaries; never infer agency identity or enable alerts."""
import copy


def selected_candidate(data, indices):
    sequence=data.get('sequence',[])
    indices=sorted(set(indices))
    if len(indices) not in (1,2) or any(i<0 or i>=len(sequence) for i in indices):
        raise ValueError('Select one run for a long tone or two neighboring runs for a two-tone page.')
    if len(indices)==2 and indices[1]!=indices[0]+1:
        raise ValueError('Select neighboring runs. Do not pair across another tone.')
    a=sequence[indices[0]];b=sequence[indices[1]] if len(indices)==2 else None
    if b and a['hz']==b['hz']:
        raise ValueError('The selected runs have identical frequencies; review whether they are one interrupted tone.')
    if b and 'gap_before' not in b:
        raise ValueError('This older observation did not save gap measurements. Capture or analyze it again before splitting.')
    result=copy.deepcopy(data)
    result.update(kind='two' if b else 'long',a_hz=a['hz'],b_hz=b['hz'] if b else None,
                  a_seconds=a['seconds'],b_seconds=b['seconds'] if b else None,
                  gap_seconds=b['gap_before'] if b else 0,
                  quality=min(a.get('quality',data['quality']),b.get('quality',data['quality'])) if b else a.get('quality',data['quality']),
                  manual_boundaries=indices,ambiguous=False)
    return result
