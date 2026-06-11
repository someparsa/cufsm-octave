% Headless CUFSM signature-curve example.
% Defines a lipped channel under uniform compression, calculates the lowest
% buckling eigenvalue over a range of half-wavelengths, and writes a compact
% text report for CLI use.

%% Environment
clear all
clc

% Resolve dependencies relative to this file for cross-platform execution.
location=fileparts(mfilename('fullpath'));
addpath(location);
addpath(fullfile(location,'analysis'));
addpath(fullfile(location,'analysis','cFSM'));
addpath(fullfile(location,'cutwp'));
addpath(fullfile(location,'helpers'));

%% Model Definition
% prop: [material_id Ex Ey nu_x nu_y G]
prop=[100 29500.00 29500.00 0.30 0.30 11346.15];

% node: [node_id x z dof_x dof_z dof_y dof_rotation stress]
node=[1 5.00 1.00 1 1 1 1 33.33
    2 5.00 0.00 1 1 1 1 50.00
    3 2.50 0.00 1 1 1 1 50.00
    4 0.00 0.00 1 1 1 1 50.00
    5 0.00 3.00 1 1 1 1 16.67
    6 0.00 6.00 1 1 1 1 -16.67
    7 0.00 9.00 1 1 1 1 -50.00
    8 2.50 9.00 1 1 1 1 -50.00
    9 5.00 9.00 1 1 1 1 -50.00
    10 5.00 8.00 1 1 1 1 -33.33];

% elem: [element_id node_i node_j thickness material_id]
elem=[1 1 2 0.100000 100
    2 2 3 0.100000 100
    3 3 4 0.100000 100
    4 4 5 0.100000 100
    5 5 6 0.100000 100
    6 6 7 0.100000 100
    7 7 8 0.100000 100
    8 8 9 0.100000 100
    9 9 10 0.100000 100];

%% Reference Loading
% Refine the section mesh before calculating section properties.
[node,elem]=doubler(node,elem);

% Generate uniform compression at the reference yield stress.
[A,xcg,zcg,Ixx,Izz,Ixz,thetap,I11,I22,J,Xs,Ys,Cw,B1,B2,w] = cutwp_prop2(node(:,2:3),elem(:,2:4));
thetap=thetap*180/pi; % Principal-axis angle in degrees.
Bx=NaN; By=NaN;
fy=50;
unsymmetric=0; % Restrained bending calculation.
[P,Mxx,Mzz,M11,M22]=yieldMP(node,fy,A,xcg,zcg,Ixx,Izz,Ixz,thetap,I11,I22,unsymmetric);
node=stresgen(node,P*1,Mxx*0,Mzz*0,M11*0,M22*0,A,xcg,zcg,Ixx,Izz,Ixz,thetap,I11,I22,unsymmetric);

%% Analysis Configuration
% For an S-S signature curve, lengths are buckling half-wavelengths.
lengths=logspace(0,3,100)';

% Supported values: S-S, C-C, S-C, C-F, and C-G.
% Signature-curve analysis requires S-S boundary conditions.
BC='S-S';

% One longitudinal term is used at each half-wavelength.
for i=1:length(lengths)
    m_all{i}=[1];
end

% No springs or multipoint constraints are applied in this example.
springs=0;
constraints=0;

neigs=10;

%% cFSM Configuration
% Initialize modal families but leave all cFSM constraints disabled.
nnodes = length(node(:,1));
ndof_m= 4*nnodes;
GBTcon.ospace=1;GBTcon.couple=1;GBTcon.orth=2;GBTcon.norm=1;
[elprop,m_node,m_elem,node_prop,nmno,ncno,nsno,ndm,nlm,DOFperm]=base_properties(node,elem);
ngm=4;nom=2*(length(node(:,1))-1);
GBTcon.local=zeros(1,nlm);
GBTcon.dist=zeros(1,ndm);
GBTcon.glob=zeros(1,ngm);
GBTcon.other=zeros(1,nom);

%% Solve
[curve,shapes]=stripmain(prop,node,elem,lengths,springs,constraints,GBTcon,BC,m_all,neigs);
clas=0;

%% CLI Report
% Report the lowest eigenvalue at each half-wavelength. Mode shapes are
% intentionally omitted because they are large and not useful in text form.
signature_curve=zeros(length(curve),2);
for i=1:length(curve)
    signature_curve(i,:)=curve{i}(1,1:2);
end

local_minima=[];
for i=2:size(signature_curve,1)-1
    if signature_curve(i,2)<signature_curve(i-1,2) && ...
            signature_curve(i,2)<signature_curve(i+1,2)
        local_minima=[local_minima; signature_curve(i,:)];
    end
end
[critical_load_factor,critical_index]=min(signature_curve(:,2));
critical_length=signature_curve(critical_index,1);

output_file=fullfile(location,'cufsm-results.txt');
fid=fopen(output_file,'w');
if fid<0
    error('Unable to open output file: %s',output_file);
end

fprintf(fid,'CUFSM CLI Analysis Results\n');
fprintf(fid,'==========================\n\n');

fprintf(fid,'MODEL\n');
fprintf(fid,'Material columns: material_id Ex Ey nu_x nu_y G\n');
fprintf(fid,'material_id,Ex,Ey,nu_x,nu_y,G\n');
for i=1:size(prop,1)
    fprintf(fid,'%.12g,%.12g,%.12g,%.12g,%.12g,%.12g\n',prop(i,:));
end

fprintf(fid,'\nNode columns: node_id x z dof_x dof_z dof_y dof_rotation stress\n');
fprintf(fid,'node_id,x,z,dof_x,dof_z,dof_y,dof_rotation,stress\n');
for i=1:size(node,1)
    fprintf(fid,'%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g\n',node(i,:));
end

fprintf(fid,'\nElement columns: element_id node_i node_j thickness material_id\n');
fprintf(fid,'element_id,node_i,node_j,thickness,material_id\n');
for i=1:size(elem,1)
    fprintf(fid,'%.12g,%.12g,%.12g,%.12g,%.12g\n',elem(i,:));
end

fprintf(fid,'\nANALYSIS SETTINGS\n');
fprintf(fid,'boundary_condition,%s\n',BC);
fprintf(fid,'number_of_lengths,%d\n',length(lengths));
fprintf(fid,'minimum_length,%.12g\n',min(lengths));
fprintf(fid,'maximum_length,%.12g\n',max(lengths));
fprintf(fid,'requested_eigenmodes,%d\n',neigs);
fprintf(fid,'springs_defined,%d\n',~(isscalar(springs) && springs==0));
fprintf(fid,'constraints_defined,%d\n',~(isscalar(constraints) && constraints==0));
fprintf(fid,'cfsm_active,%d\n',any([GBTcon.local GBTcon.dist GBTcon.glob GBTcon.other]));

fprintf(fid,'\nSIGNATURE CURVE\n');
fprintf(fid,'half_wavelength,lowest_eigenvalue\n');
for i=1:size(signature_curve,1)
    fprintf(fid,'%.12g,%.12g\n',signature_curve(i,1),signature_curve(i,2));
end

fprintf(fid,'\nCRITICAL POINTS\n');
fprintf(fid,'type,half_wavelength,lowest_eigenvalue\n');
fprintf(fid,'overall_minimum,%.12g,%.12g\n',critical_length,critical_load_factor);
for i=1:size(local_minima,1)
    fprintf(fid,'local_minimum,%.12g,%.12g\n',local_minima(i,1),local_minima(i,2));
end

fclose(fid);
fprintf('Results written to %s\n',output_file);
