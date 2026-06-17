function cufsm_json_run(input_file)
%CUFSM_JSON Run a headless CUFSM signature-curve analysis from a JSON file.
if nargin < 1 || isempty(input_file)
    error('Usage: octave-cli --quiet cufsm_json.m path/to/input.json');
end
helper_location = fileparts(mfilename('fullpath'));
if isempty(helper_location)
    helper_location = pwd;
end
location = fileparts(helper_location);

addpath(location);
addpath(fullfile(location,'analysis'));
addpath(fullfile(location,'analysis','cFSM'));
addpath(fullfile(location,'cutwp'));
addpath(fullfile(location,'helpers'));

raw_json = fileread(input_file);
cfg = jsondecode(raw_json);

if ~isfield(cfg,'version')
    error('JSON input must include a version field.');
end
if ~isfield(cfg,'model')
    error('JSON input must include a model object.');
end
if ~isfield(cfg,'analysis')
    error('JSON input must include an analysis object.');
end

prop = materials_to_matrix(cfg.model.materials);
node = nodes_to_matrix(cfg.model.nodes);
elem = elements_to_matrix(cfg.model.elements);

validate_model(prop,node,elem);

if isfield(cfg.analysis,'mesh_refinement') && ...
        isfield(cfg.analysis.mesh_refinement,'doubler') && ...
        logical(cfg.analysis.mesh_refinement.doubler)
    [node,elem] = doubler(node,elem);
end

loading_type = 'stress_table';
if isfield(cfg,'loading') && isfield(cfg.loading,'type')
    loading_type = cfg.loading.type;
end

if strcmp(loading_type,'generated_from_actions')
    fy = require_number(cfg.loading,'fy','loading.fy');
    unsymmetric = optional_bool(cfg.loading,'unsymmetric',false);
    [A,xcg,zcg,Ixx,Izz,Ixz,thetap,I11,I22,J,Xs,Ys,Cw,B1,B2,w] = ...
        cutwp_prop2(node(:,2:3),elem(:,2:4));
    thetap = thetap * 180 / pi;
    [Py,Mxx_y,Mzz_y,M11_y,M22_y] = ...
        yieldMP(node,fy,A,xcg,zcg,Ixx,Izz,Ixz,thetap,I11,I22,unsymmetric);
    actions = cfg.loading.actions;
    P = optional_number(actions,'P',optional_number(actions,'P_factor',0) * Py);
    Mxx = optional_number(actions,'Mxx',optional_number(actions,'Mxx_factor',0) * Mxx_y);
    Mzz = optional_number(actions,'Mzz',optional_number(actions,'Mzz_factor',0) * Mzz_y);
    M11 = optional_number(actions,'M11',optional_number(actions,'M11_factor',0) * M11_y);
    M22 = optional_number(actions,'M22',optional_number(actions,'M22_factor',0) * M22_y);
    node = stresgen(node,P,Mxx,Mzz,M11,M22,A,xcg,zcg,Ixx,Izz,Ixz,thetap,I11,I22,unsymmetric);
elseif strcmp(loading_type,'stress_table')
    % Stresses are already in node(:,8).
else
    error('Unsupported loading.type: %s',loading_type);
end

analysis_type = optional_string(cfg.analysis,'type','signature_curve');
if ~strcmp(analysis_type,'signature_curve')
    error('Only analysis.type="signature_curve" is currently supported.');
end

BC = require_string(cfg.analysis,'boundary_condition','analysis.boundary_condition');
valid_BC = {'S-S','C-C','S-C','C-F','C-G'};
if ~any(strcmp(BC,valid_BC))
    error('Unsupported boundary_condition: %s',BC);
end

[lengths,member_lengths] = build_lengths(cfg.analysis.lengths);
m_all = build_longitudinal_terms(cfg.analysis, length(lengths));
springs = optional_table(cfg.model,'springs');
constraints = optional_table(cfg.model,'constraints');
neigs = optional_number(cfg.analysis,'eigenmodes',20);
ifVec = optional_bool(cfg.analysis,'vectorized',false);
GBTcon = build_cfsm(cfg.analysis,node,elem,prop,BC,m_all);

[curve,shapes] = stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,neigs,ifVec);

signature_curve = zeros(length(curve),2);
for i = 1:length(curve)
    signature_curve(i,:) = curve{i}(1,1:2);
end

warning_state = warning('off','all');
clas = classify_headless(prop,node,elem,lengths,shapes,GBTcon,BC,m_all);
warning(warning_state);
lowest_mode_participation = build_lowest_mode_participation(curve,clas);

local_minima = [];
local_minima_classified = [];
for i = 2:size(signature_curve,1)-1
    if signature_curve(i,2) < signature_curve(i-1,2) && ...
            signature_curve(i,2) < signature_curve(i+1,2)
        local_minima = [local_minima; signature_curve(i,:)];
        local_minima_classified = [local_minima_classified; ...
            classified_point_row(i,signature_curve(i,1),signature_curve(i,2),clas{i}(1,:))];
    end
end
[critical_load_factor,critical_index] = min(signature_curve(:,2));
critical_length = signature_curve(critical_index,1);
overall_minimum_classified = classified_point_row(critical_index,critical_length,critical_load_factor,clas{critical_index}(1,:));
family_minima = build_family_minima(local_minima_classified);
member_mode_participation = build_requested_mode_participation(member_lengths,lengths,curve,clas);
minimum_mode_participation = build_minimum_mode_participation(local_minima,lengths,curve,clas);

output_cfg = struct();
if isfield(cfg,'output')
    output_cfg = cfg.output;
end
output_path = optional_string(output_cfg,'path','cufsm-results.json');
if ~is_absolute_path(output_path)
    output_path = fullfile(location,output_path);
end

[A,xcg,zcg,Ixx,Izz,Ixz,thetap,I11,I22,J,Xs,Ys,Cw,B1,B2,w] = ...
    cutwp_prop2(node(:,2:3),elem(:,2:4));
section_properties = struct( ...
    'area',A, ...
    'centroid_x',xcg, ...
    'centroid_z',zcg, ...
    'Ixx',Ixx, ...
    'Izz',Izz, ...
    'Ixz',Ixz, ...
    'theta_principal_radians',thetap, ...
    'I11',I11, ...
    'I22',I22, ...
    'J',J, ...
    'shear_center_x',Xs, ...
    'shear_center_z',Ys, ...
    'Cw',Cw, ...
    'B1',B1, ...
    'B2',B2);

results = struct();
results.version = cfg.version;
results.analysis_type = analysis_type;
results.model = struct('materials',prop,'nodes',node,'elements',elem);
results.analysis_settings = struct( ...
    'boundary_condition',BC, ...
    'number_of_lengths',length(lengths), ...
    'minimum_length',min(lengths), ...
    'maximum_length',max(lengths), ...
    'requested_eigenmodes',neigs, ...
    'member_lengths',member_lengths, ...
    'vectorized',ifVec, ...
    'springs_defined',~(isscalar(springs) && springs == 0), ...
    'constraints_defined',~(isscalar(constraints) && constraints == 0), ...
    'cfsm_active',any([GBTcon.local GBTcon.dist GBTcon.glob GBTcon.other]));
results.section_properties = section_properties;
results.signature_curve = signature_curve;
results.critical_points = struct( ...
    'overall_minimum',[critical_length critical_load_factor], ...
    'overall_minimum_classified',overall_minimum_classified, ...
    'local_minima',local_minima, ...
    'local_minima_classified',local_minima_classified, ...
    'family_minima',family_minima);
results.mode_participation = struct( ...
    'family_labels',{{'global','distortional','local','other'}}, ...
    'table_columns',{{'length','eigenvalue','global_percent','distortional_percent','local_percent','other_percent','dominant_family_id'}}, ...
    'lowest_modes',lowest_mode_participation, ...
    'participation_point_columns',{{'requested_length','matched_length','length_index','mode_number','eigenvalue','global_percent','distortional_percent','local_percent','other_percent','dominant_family_id'}}, ...
    'member_lengths',member_mode_participation, ...
    'signature_minima',minimum_mode_participation);

fid = fopen(output_path,'w');
if fid < 0
    error('Unable to open output file: %s',output_path);
end
fprintf(fid,'%s\n',jsonencode(results));
fclose(fid);

if isfield(output_cfg,'text_path')
    text_path = output_cfg.text_path;
    if ~is_absolute_path(text_path)
        text_path = fullfile(location,text_path);
    end
    write_text_report(text_path,prop,node,elem,BC,lengths,member_lengths,neigs,springs,constraints,GBTcon,signature_curve,critical_length,critical_load_factor,local_minima,local_minima_classified,family_minima,lowest_mode_participation,member_mode_participation,minimum_mode_participation);
end

fprintf('JSON results written to %s\n',output_path);

function prop = materials_to_matrix(materials)
    n = length(materials);
    prop = zeros(n,6);
    for i = 1:n
        m = materials(i);
        prop(i,:) = [m.id m.Ex m.Ey m.nu_x m.nu_y m.G];
    end
end

function node = nodes_to_matrix(nodes)
    n = length(nodes);
    node = zeros(n,8);
    for i = 1:n
        nd = nodes(i);
        node(i,:) = [nd.id nd.x nd.z nd.dof_x nd.dof_z nd.dof_y nd.dof_rotation nd.stress];
    end
end

function elem = elements_to_matrix(elements)
    n = length(elements);
    elem = zeros(n,5);
    for i = 1:n
        el = elements(i);
        elem(i,:) = [el.id el.node_i el.node_j el.thickness el.material_id];
    end
end

function validate_model(prop,node,elem)
    if size(prop,2) ~= 6
        error('materials must convert to an n x 6 prop matrix.');
    end
    if size(node,2) ~= 8
        error('nodes must convert to an n x 8 node matrix.');
    end
    if size(elem,2) ~= 5
        error('elements must convert to an n x 5 elem matrix.');
    end
    if length(unique(prop(:,1))) ~= size(prop,1)
        error('material ids must be unique.');
    end
    if length(unique(node(:,1))) ~= size(node,1)
        error('node ids must be unique.');
    end
    if length(unique(elem(:,1))) ~= size(elem,1)
        error('element ids must be unique.');
    end
    if any(elem(:,4) <= 0)
        error('element thickness values must be positive.');
    end
    for i = 1:size(elem,1)
        if ~any(node(:,1) == elem(i,2)) || ~any(node(:,1) == elem(i,3))
            error('element %g references a missing node.',elem(i,1));
        end
        if ~any(prop(:,1) == elem(i,5))
            error('element %g references a missing material.',elem(i,1));
        end
    end
end

function [lengths,member_lengths] = build_lengths(length_cfg)
    length_type = optional_string(length_cfg,'type','explicit');
    member_lengths = optional_numeric_vector(length_cfg,'member_lengths',[]);
    if strcmp(length_type,'logspace')
        mn = require_number(length_cfg,'min','analysis.lengths.min');
        mx = require_number(length_cfg,'max','analysis.lengths.max');
        cnt = require_number(length_cfg,'count','analysis.lengths.count');
        lengths = logspace(log10(mn),log10(mx),cnt)';
    elseif strcmp(length_type,'linspace')
        mn = require_number(length_cfg,'min','analysis.lengths.min');
        mx = require_number(length_cfg,'max','analysis.lengths.max');
        cnt = require_number(length_cfg,'count','analysis.lengths.count');
        lengths = linspace(mn,mx,cnt)';
    elseif strcmp(length_type,'explicit')
        lengths = numeric_vector(length_cfg.values)';
    else
        error('Unsupported analysis.lengths.type: %s',length_type);
    end
    if any(member_lengths <= 0)
        error('All member_lengths must be positive.');
    end
    lengths = unique([lengths(:); member_lengths(:)]);
    if any(lengths <= 0)
        error('All lengths must be positive.');
    end
end

function m_all = build_longitudinal_terms(analysis,nlengths)
    if ~isfield(analysis,'longitudinal_terms')
        terms = [1];
        for i = 1:nlengths
            m_all{i} = terms;
        end
        return
    end
    lt = analysis.longitudinal_terms;
    if isfield(lt,'default')
        terms = numeric_vector(lt.default);
        for i = 1:nlengths
            m_all{i} = terms;
        end
    elseif isfield(lt,'per_length')
        if length(lt.per_length) ~= nlengths
            error('analysis.longitudinal_terms.per_length must match the number of lengths.');
        end
        for i = 1:nlengths
            m_all{i} = numeric_vector(lt.per_length(i).terms);
        end
    else
        error('analysis.longitudinal_terms must define default or per_length.');
    end
end

function GBTcon = build_cfsm(analysis,node,elem,prop,BC,m_all)
    cfsm = struct();
    if isfield(analysis,'cfsm')
        cfsm = analysis.cfsm;
    end
    [elprop,m_node,m_elem,node_prop,nmno,ncno,nsno,ndm,nlm,DOFperm] = base_properties(node,elem);
    ngm = 4;
    nom = 2*(length(node(:,1))-1);
    GBTcon.ospace = optional_number(cfsm,'ospace',1);
    GBTcon.couple = optional_number(cfsm,'couple',1);
    GBTcon.orth = optional_number(cfsm,'orth',2);
    GBTcon.norm = optional_number(cfsm,'norm',1);
    GBTcon.local = sized_mode_vector(cfsm,'local',nlm);
    GBTcon.dist = sized_mode_vector(cfsm,'distortional',ndm);
    GBTcon.glob = sized_mode_vector(cfsm,'global',ngm);
    GBTcon.other = sized_mode_vector(cfsm,'other',nom);
end

function out = sized_mode_vector(s,name,n)
    out = zeros(1,n);
    if isfield(s,name)
        values = numeric_vector(s.(name));
        if isempty(values)
            return
        end
        if length(values) == n && all(values == 0 | values == 1)
            out = values(:)';
        else
            for i = 1:length(values)
                idx = values(i);
                if idx < 1 || idx > n
                    error('cfsm.%s contains out-of-range mode index %g.',name,idx);
                end
                out(idx) = 1;
            end
        end
    end
end

function table = optional_table(parent,name)
    if ~isfield(parent,name) || isempty(parent.(name))
        table = 0;
        return
    end
    value = parent.(name);
    if isnumeric(value)
        table = value;
    elseif isstruct(value) && strcmp(name,'springs')
        table = springs_to_matrix(value);
    elseif isstruct(value) && strcmp(name,'constraints')
        table = constraints_to_matrix(value);
    else
        error('model.%s must be an empty array, numeric matrix, or supported object array.',name);
    end
end

function springs = springs_to_matrix(items)
    springs = zeros(length(items),4);
    for i = 1:length(items)
        item = items(i);
        springs(i,:) = [item.node item.dof item.stiffness item.kflag];
    end
end

function constraints = constraints_to_matrix(items)
    constraints = zeros(length(items),5);
    for i = 1:length(items)
        item = items(i);
        constraints(i,:) = [item.node_e item.dof_e item.coefficient item.node_k item.dof_k];
    end
end

function value = require_number(s,name,label)
    if ~isfield(s,name)
        error('Missing required number: %s',label);
    end
    value = s.(name);
end

function value = require_string(s,name,label)
    if ~isfield(s,name)
        error('Missing required string: %s',label);
    end
    value = s.(name);
end

function value = optional_number(s,name,default_value)
    if isstruct(s) && isfield(s,name) && ~isempty(s.(name))
        value = s.(name);
    else
        value = default_value;
    end
end

function value = optional_string(s,name,default_value)
    if isstruct(s) && isfield(s,name) && ~isempty(s.(name))
        value = s.(name);
    else
        value = default_value;
    end
end

function value = optional_bool(s,name,default_value)
    if isstruct(s) && isfield(s,name) && ~isempty(s.(name))
        value = logical(s.(name));
    else
        value = default_value;
    end
end

function value = optional_numeric_vector(s,name,default_value)
    if isstruct(s) && isfield(s,name) && ~isempty(s.(name))
        value = numeric_vector(s.(name));
    else
        value = default_value;
    end
end

function out = numeric_vector(value)
    if isempty(value)
        out = [];
    else
        out = value(:)';
    end
end

function tf = is_absolute_path(path_value)
    if isempty(path_value)
        tf = false;
    elseif path_value(1) == '/'
        tf = true;
    elseif length(path_value) >= 3 && path_value(2) == ':' && (path_value(3) == '\' || path_value(3) == '/')
        tf = true;
    else
        tf = false;
    end
end


function clas = classify_headless(prop,node,elem,lengths,shapes,GBTcon,BC,m_all)
    nnodes = length(node(:,1));
    ndof_m = 4 * nnodes;
    [m_all] = msort(m_all);
    clas = cell(length(lengths),1);
    for l = 1:length(lengths)
        a = lengths(l);
        m_a = m_all{l};
        [b_v_l,ngm,ndm,nlm] = base_column(node,elem,prop,a,BC,m_a);
        b_v = base_update(GBTcon.ospace,GBTcon.norm,b_v_l,a,m_a,node,elem,prop,ngm,ndm,nlm,BC,GBTcon.couple,GBTcon.orth);
        clas{l} = zeros(size(shapes{l},2),4);
        for mod = 1:size(shapes{l},2)
            clas{l}(mod,1:4) = mode_class(b_v,shapes{l}(:,mod),ngm,ndm,nlm,m_a,ndof_m,GBTcon.couple);
        end
    end
end

function table = build_lowest_mode_participation(curve,clas)
    table = zeros(length(curve),7);
    for i = 1:length(curve)
        parts = clas{i}(1,:);
        table(i,:) = [curve{i}(1,1) curve{i}(1,2) parts dominant_family_id(parts)];
    end
end

function row = classified_point_row(index_value,length_value,eigenvalue,parts)
    row = [length_value eigenvalue index_value parts dominant_family_id(parts)];
end

function family_id = dominant_family_id(parts)
    [mx,family_id] = max(parts);
    if isempty(mx) || mx <= 0
        family_id = 0;
    end
end

function family_minima = build_family_minima(local_minima_classified)
    family_minima = [];
    if isempty(local_minima_classified)
        return
    end
    for family_id = 1:4
        rows = local_minima_classified(local_minima_classified(:,8) == family_id,:);
        if ~isempty(rows)
            [mn,idx] = min(rows(:,2));
            best = rows(idx,:);
            family_minima = [family_minima; family_id best(1:7)];
        end
    end
end

function table = build_minimum_mode_participation(local_minima,lengths,curve,clas)
    if isempty(local_minima)
        table = [];
    else
        table = build_requested_mode_participation(local_minima(:,1),lengths,curve,clas);
    end
end

function table = build_requested_mode_participation(requested_lengths,lengths,curve,clas)
    table = [];
    for r = 1:length(requested_lengths)
        requested_length = requested_lengths(r);
        [delta,length_index] = min(abs(lengths - requested_length));
        matched_length = lengths(length_index);
        for mode_number = 1:size(curve{length_index},1)
            eigenvalue = curve{length_index}(mode_number,2);
            parts = clas{length_index}(mode_number,:);
            table = [table; requested_length matched_length length_index mode_number eigenvalue parts dominant_family_id(parts)];
        end
    end
end

function label = family_label(family_id)
    labels = {'global','distortional','local','other'};
    if family_id >= 1 && family_id <= 4
        label = labels{family_id};
    else
        label = 'unknown';
    end
end

function write_text_report(output_file,prop,node,elem,BC,lengths,member_lengths,neigs,springs,constraints,GBTcon,signature_curve,critical_length,critical_load_factor,local_minima,local_minima_classified,family_minima,lowest_mode_participation,member_mode_participation,minimum_mode_participation)
    fid = fopen(output_file,'w');
    if fid < 0
        error('Unable to open output file: %s',output_file);
    end
    fprintf(fid,'CUFSM CLI Analysis Results\n');
    fprintf(fid,'==========================\n\n');
    fprintf(fid,'MODEL\n');
    fprintf(fid,'Material columns: material_id Ex Ey nu_x nu_y G\n');
    fprintf(fid,'material_id,Ex,Ey,nu_x,nu_y,G\n');
    for i = 1:size(prop,1)
        fprintf(fid,'%.12g,%.12g,%.12g,%.12g,%.12g,%.12g\n',prop(i,:));
    end
    fprintf(fid,'\nNode columns: node_id x z dof_x dof_z dof_y dof_rotation stress\n');
    fprintf(fid,'node_id,x,z,dof_x,dof_z,dof_y,dof_rotation,stress\n');
    for i = 1:size(node,1)
        fprintf(fid,'%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g\n',node(i,:));
    end
    fprintf(fid,'\nElement columns: element_id node_i node_j thickness material_id\n');
    fprintf(fid,'element_id,node_i,node_j,thickness,material_id\n');
    for i = 1:size(elem,1)
        fprintf(fid,'%.12g,%.12g,%.12g,%.12g,%.12g\n',elem(i,:));
    end
    fprintf(fid,'\nANALYSIS SETTINGS\n');
    fprintf(fid,'boundary_condition,%s\n',BC);
    fprintf(fid,'number_of_lengths,%d\n',length(lengths));
    fprintf(fid,'minimum_length,%.12g\n',min(lengths));
    fprintf(fid,'maximum_length,%.12g\n',max(lengths));
    fprintf(fid,'requested_eigenmodes,%d\n',neigs);
    fprintf(fid,'member_lengths');
    for i = 1:length(member_lengths)
        fprintf(fid,',%.12g',member_lengths(i));
    end
    fprintf(fid,'\n');
    fprintf(fid,'springs_defined,%d\n',~(isscalar(springs) && springs == 0));
    fprintf(fid,'constraints_defined,%d\n',~(isscalar(constraints) && constraints == 0));
    fprintf(fid,'cfsm_active,%d\n',any([GBTcon.local GBTcon.dist GBTcon.glob GBTcon.other]));
    fprintf(fid,'\nSIGNATURE CURVE\n');
    fprintf(fid,'half_wavelength,lowest_eigenvalue\n');
    for i = 1:size(signature_curve,1)
        fprintf(fid,'%.12g,%.12g\n',signature_curve(i,1),signature_curve(i,2));
    end
    fprintf(fid,'\nCRITICAL POINTS\n');
    fprintf(fid,'type,half_wavelength,lowest_eigenvalue\n');
    fprintf(fid,'overall_minimum,%.12g,%.12g\n',critical_length,critical_load_factor);
    for i = 1:size(local_minima,1)
        fprintf(fid,'local_minimum,%.12g,%.12g\n',local_minima(i,1),local_minima(i,2));
    end
    fprintf(fid,'\nCLASSIFIED LOCAL MINIMA\n');
    fprintf(fid,'type,half_wavelength,lowest_eigenvalue,length_index,global_percent,distortional_percent,local_percent,other_percent,dominant_family\n');
    for i = 1:size(local_minima_classified,1)
        fprintf(fid,'local_minimum,%.12g,%.12g,%d,%.12g,%.12g,%.12g,%.12g,%s\n', ...
            local_minima_classified(i,1),local_minima_classified(i,2),local_minima_classified(i,3), ...
            local_minima_classified(i,4),local_minima_classified(i,5),local_minima_classified(i,6),local_minima_classified(i,7), ...
            family_label(local_minima_classified(i,8)));
    end
    fprintf(fid,'\nFAMILY MINIMA\n');
    fprintf(fid,'dominant_family,half_wavelength,lowest_eigenvalue,length_index,global_percent,distortional_percent,local_percent,other_percent\n');
    for i = 1:size(family_minima,1)
        fprintf(fid,'%s,%.12g,%.12g,%d,%.12g,%.12g,%.12g,%.12g\n', ...
            family_label(family_minima(i,1)),family_minima(i,2),family_minima(i,3),family_minima(i,4), ...
            family_minima(i,5),family_minima(i,6),family_minima(i,7),family_minima(i,8));
    end
    fprintf(fid,'\nLOWEST MODE PARTICIPATION\n');
    fprintf(fid,'half_wavelength,lowest_eigenvalue,global_percent,distortional_percent,local_percent,other_percent,dominant_family\n');
    for i = 1:size(lowest_mode_participation,1)
        fprintf(fid,'%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%s\n', ...
            lowest_mode_participation(i,1),lowest_mode_participation(i,2),lowest_mode_participation(i,3), ...
            lowest_mode_participation(i,4),lowest_mode_participation(i,5),lowest_mode_participation(i,6), ...
            family_label(lowest_mode_participation(i,7)));
    end
    if ~isempty(member_mode_participation)
        fprintf(fid,'\nMEMBER LENGTH MODE PARTICIPATION\n');
        fprintf(fid,'requested_length,matched_length,length_index,mode_number,eigenvalue,global_percent,distortional_percent,local_percent,other_percent,dominant_family\n');
        for i = 1:size(member_mode_participation,1)
            fprintf(fid,'%.12g,%.12g,%d,%d,%.12g,%.12g,%.12g,%.12g,%.12g,%s\n', ...
                member_mode_participation(i,1),member_mode_participation(i,2),member_mode_participation(i,3),member_mode_participation(i,4), ...
                member_mode_participation(i,5),member_mode_participation(i,6),member_mode_participation(i,7), ...
                member_mode_participation(i,8),member_mode_participation(i,9),family_label(member_mode_participation(i,10)));
        end
    end
    if ~isempty(minimum_mode_participation)
        fprintf(fid,'\nSIGNATURE MINIMA MODE PARTICIPATION\n');
        fprintf(fid,'requested_length,matched_length,length_index,mode_number,eigenvalue,global_percent,distortional_percent,local_percent,other_percent,dominant_family\n');
        for i = 1:size(minimum_mode_participation,1)
            fprintf(fid,'%.12g,%.12g,%d,%d,%.12g,%.12g,%.12g,%.12g,%.12g,%s\n', ...
                minimum_mode_participation(i,1),minimum_mode_participation(i,2),minimum_mode_participation(i,3),minimum_mode_participation(i,4), ...
                minimum_mode_participation(i,5),minimum_mode_participation(i,6),minimum_mode_participation(i,7), ...
                minimum_mode_participation(i,8),minimum_mode_participation(i,9),family_label(minimum_mode_participation(i,10)));
        end
    end
    fclose(fid);
end
end
