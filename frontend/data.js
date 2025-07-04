const patients = [
  {
    id: 'p1',
    name: 'John Doe',
    mrn: 'MRN001',
    birthdate: '1950-03-12',
    scans: [
      { date: '2024-04-01', file: 'scans/john1.nii.gz', hasSegmentation: true, reportAvailable: true },
      { date: '2023-12-15', file: 'scans/john2.nii.gz', hasSegmentation: true, reportAvailable: false }
    ]
  },
  {
    id: 'p2',
    name: 'Jane Smith',
    mrn: 'MRN002',
    birthdate: '1948-07-22',
    scans: [
      { date: '2024-03-10', file: 'scans/jane1.nii.gz', hasSegmentation: false, reportAvailable: false },
      { date: '2023-11-05', file: 'scans/jane2.nii.gz', hasSegmentation: false, reportAvailable: false }
    ]
  },
  {
    id: 'p3',
    name: 'Albert Lee',
    mrn: 'MRN003',
    birthdate: '1955-01-30',
    scans: [
      { date: '2024-02-20', file: 'scans/albert1.nii.gz', hasSegmentation: true, reportAvailable: true },
      { date: '2023-10-18', file: 'scans/albert2.nii.gz', hasSegmentation: true, reportAvailable: true }
    ]
  },
  {
    id: 'p4',
    name: 'Maria Garcia',
    mrn: 'MRN004',
    birthdate: '1952-11-09',
    scans: [
      { date: '2024-01-15', file: 'scans/maria1.nii.gz', hasSegmentation: false, reportAvailable: false }
    ]
  },
  {
    id: 'p5',
    name: 'Robert Brown',
    mrn: 'MRN005',
    birthdate: '1949-05-17',
    scans: [
      { date: '2024-03-28', file: 'scans/robert1.nii.gz', hasSegmentation: true, reportAvailable: true },
      { date: '2023-09-12', file: 'scans/robert2.nii.gz', hasSegmentation: false, reportAvailable: false }
    ]
  }
]; 